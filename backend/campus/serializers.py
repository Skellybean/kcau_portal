from django.conf import settings
from rest_framework import serializers

from accounts.models import Role, User

from .models import Announcement, Facility, Result, TimetableSlot, Unit


class UnitSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.CharField(source="lecturer.full_name", read_only=True, default=None)
    registered = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ["id", "code", "title", "description", "credits", "lecturer", "lecturer_name", "registered"]

    def get_registered(self, unit):
        """True when the student registered for this unit on the portal this trimester."""
        user = self.context["request"].user
        if not user.is_student:
            return None
        registered_ids = self.context.get("registered_ids")
        if registered_ids is None:
            return unit.enrollments.filter(student=user, trimester=settings.CURRENT_TRIMESTER).exists()
        return unit.id in registered_ids


class TimetableSlotSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)
    day_name = serializers.CharField(source="get_day_display", read_only=True)

    class Meta:
        model = TimetableSlot
        fields = ["id", "unit", "unit_code", "unit_title", "day", "day_name", "start_time", "end_time", "venue"]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs


class ResultSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)
    credits = serializers.IntegerField(source="unit.credits", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    total = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    grade = serializers.CharField(read_only=True)

    class Meta:
        model = Result
        fields = [
            "id", "student", "student_name", "unit", "unit_code", "unit_title", "credits",
            "cat_mark", "exam_mark", "total", "grade", "academic_year",
        ]

    def validate_student(self, student):
        if student.role != Role.STUDENT:
            raise serializers.ValidationError("Results can only be recorded for students.")
        return student

    def validate_cat_mark(self, value):
        if not 0 <= value <= 30:
            raise serializers.ValidationError("CAT mark must be between 0 and 30.")
        return value

    def validate_exam_mark(self, value):
        if not 0 <= value <= 70:
            raise serializers.ValidationError("Exam mark must be between 0 and 70.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        unit = attrs.get("unit") or getattr(self.instance, "unit", None)
        if request.user.is_lecturer and unit and unit.lecturer_id != request.user.id:
            raise serializers.ValidationError("You can only record results for units you teach.")
        return attrs


class AnnouncementSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True, default=None)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = ["id", "title", "body", "audience", "pinned", "author_name", "created_at", "can_edit"]
        read_only_fields = ["created_at"]

    def get_can_edit(self, obj):
        user = self.context["request"].user
        return user.is_admin_role or (user.is_lecturer and obj.author_id == user.id)

    def validate_pinned(self, value):
        if value and not self.context["request"].user.is_admin_role:
            raise serializers.ValidationError("Only administrators can pin announcements.")
        return value


class FacilitySerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Facility
        fields = ["id", "name", "category", "category_label", "description", "location", "opening_hours", "contact"]
