"""Fee status, assessments (CATs and assignments), submissions and exam timetable.

Imported at the bottom of campus/models.py so Django registers these models
under the ``campus`` app.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class FeeStatus(models.Model):
    """Whether a student's school fees are cleared. Sent by the KCA portal.

    Keyed by email so a status can arrive before the student has an account.
    A student with no row is treated as NOT cleared.
    """

    email = models.EmailField(unique=True)
    cleared = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["email"]
        verbose_name_plural = "fee statuses"

    def __str__(self):
        return f"{self.email}: {'cleared' if self.cleared else 'outstanding'}"


class AssessmentKind(models.TextChoices):
    CAT = "cat", "CAT"
    ASSIGNMENT = "assignment", "Assignment"


class Assessment(models.Model):
    """A CAT or assignment that students submit in the Virtual Campus."""

    unit = models.ForeignKey("campus.Unit", on_delete=models.CASCADE, related_name="assessments")
    kind = models.CharField(max_length=12, choices=AssessmentKind.choices, default=AssessmentKind.ASSIGNMENT)
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    due_at = models.DateTimeField()
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    allow_text = models.BooleanField(default=True)
    allow_file = models.BooleanField(default=True)
    accept_late = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assessments_created",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["due_at"]

    def clean(self):
        if not (self.allow_text or self.allow_file):
            raise ValidationError("Allow a typed answer, a file upload, or both.")
        if self.max_marks is not None and self.max_marks <= 0:
            raise ValidationError({"max_marks": "Maximum marks must be above zero."})

    @property
    def accepting(self):
        """True while students may still submit."""
        return self.accept_late or timezone.now() <= self.due_at

    def __str__(self):
        return f"{self.unit.code} {self.get_kind_display()}: {self.title}"


class Submission(models.Model):
    """One student's answer to one assessment. A later submission replaces the earlier one.

    Files are kept in the database (small documents only) because the Render
    web service has no persistent disk.
    """

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={"role": "student"},
    )
    text_answer = models.TextField(blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    file_data = models.BinaryField(blank=True, editable=False, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        unique_together = [("assessment", "student")]

    def clean(self):
        if self.marks is not None and self.assessment_id:
            if not (0 <= self.marks <= self.assessment.max_marks):
                raise ValidationError({"marks": "Marks must be between 0 and the assessment's maximum."})

    def __str__(self):
        return f"{self.student.email} -> {self.assessment}"


class ExamSlot(models.Model):
    """One sitting of a unit's exam in a trimester."""

    unit = models.ForeignKey("campus.Unit", on_delete=models.CASCADE, related_name="exam_slots")
    trimester = models.CharField(max_length=40)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=120)

    class Meta:
        ordering = ["date", "start_time"]

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

    def __str__(self):
        return f"{self.unit.code} exam {self.date} {self.start_time:%H:%M}"
