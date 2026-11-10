from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Unit(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.PositiveSmallIntegerField(default=3)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="units_taught",
        limit_choices_to={"role": "lecturer"},
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.title}"


class Enrollment(models.Model):
    """A unit a student registered for on the KCA portal in a given trimester.

    The Virtual Campus never creates these from the app: they arrive from the
    portal (sync endpoint, CSV import or the admin site).
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "student"},
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="enrollments")
    trimester = models.CharField(max_length=40, help_text="For example: 2026 Trimester 3")
    registered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("student", "unit", "trimester")]
        ordering = ["-trimester", "unit__code"]

    def __str__(self):
        return f"{self.student.email} in {self.unit.code} ({self.trimester})"


class PendingRegistration(models.Model):
    """A portal registration for a student who has not created a Virtual Campus account yet.

    It is turned into a real Enrollment when that student verifies their KCA email.
    """

    email = models.EmailField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="pending_registrations")
    trimester = models.CharField(max_length=40)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("email", "unit", "trimester")]

    def __str__(self):
        return f"{self.email} -> {self.unit.code} ({self.trimester})"


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class ClassMode(models.TextChoices):
    IN_PERSON = "in_person", "In person"
    ONLINE = "online", "Online"
    HYBRID = "hybrid", "Hybrid"


def validate_https_link(value):
    """Class links must be https so the app never opens other kinds of link."""
    if value and not value.lower().startswith("https://"):
        raise ValidationError("The class link must start with https://")


class TimetableSlot(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="slots")
    day = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=120, blank=True, help_text="Required for in-person and hybrid classes")
    mode = models.CharField(max_length=10, choices=ClassMode.choices, default=ClassMode.IN_PERSON)
    meeting_link = models.URLField(max_length=500, blank=True, validators=[validate_https_link])
    meeting_note = models.CharField(max_length=200, blank=True, help_text="Passcode or joining instructions")

    class Meta:
        ordering = ["day", "start_time"]

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        if self.mode in (ClassMode.IN_PERSON, ClassMode.HYBRID) and not self.venue.strip():
            raise ValidationError({"venue": "A venue is required for in-person and hybrid classes."})

    def save(self, *args, **kwargs):
        # An in-person class has no link; clear it so an old link is never shown by mistake.
        if self.mode == ClassMode.IN_PERSON:
            self.meeting_link = ""
            self.meeting_note = ""
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit.code} {self.get_day_display()} {self.start_time:%H:%M}"


def grade_for(total):
    if total >= 70:
        return "A"
    if total >= 60:
        return "B"
    if total >= 50:
        return "C"
    if total >= 40:
        return "D"
    return "E"


class Result(models.Model):
    """Sample results: CAT is out of 30 and the exam out of 70."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="results",
        limit_choices_to={"role": "student"},
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="results")
    cat_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    exam_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    academic_year = models.CharField(max_length=20, default="2026/2027")
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("student", "unit", "academic_year")]
        ordering = ["-academic_year", "unit__code"]

    def clean(self):
        if self.cat_mark is not None and not (0 <= self.cat_mark <= 30):
            raise ValidationError({"cat_mark": "CAT mark must be between 0 and 30."})
        if self.exam_mark is not None and not (0 <= self.exam_mark <= 70):
            raise ValidationError({"exam_mark": "Exam mark must be between 0 and 70."})

    @property
    def total(self):
        return self.cat_mark + self.exam_mark

    @property
    def grade(self):
        return grade_for(self.total)

    def __str__(self):
        return f"{self.student.email} {self.unit.code} {self.total}"


class Audience(models.TextChoices):
    ALL = "all", "Everyone"
    STUDENTS = "students", "Students"
    LECTURERS = "lecturers", "Lecturers"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.ALL)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="announcements"
    )
    created_at = models.DateTimeField(default=timezone.now)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-created_at"]

    def __str__(self):
        return self.title


class FacilityCategory(models.TextChoices):
    ACADEMIC = "academic", "Academic"
    LIBRARY = "library", "Library and study"
    FOOD = "food", "Food and drink"
    HEALTH = "health", "Health and wellbeing"
    SERVICES = "services", "Student services"
    SPORTS = "sports", "Sports and recreation"


class Facility(models.Model):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=12, choices=FacilityCategory.choices)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, help_text="Building, floor or landmark")
    opening_hours = models.CharField(max_length=120, blank=True)
    contact = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name_plural = "facilities"

    def __str__(self):
        return self.name
