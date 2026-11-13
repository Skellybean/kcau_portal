from rest_framework import serializers

from .models_coursework import Assessment, ExamSlot, Submission


class AssessmentSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    accepting = serializers.BooleanField(read_only=True)
    my_submission = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            "id", "unit", "unit_code", "unit_title", "kind", "kind_label", "title", "instructions",
            "due_at", "max_marks", "allow_text", "allow_file", "accept_late", "accepting", "my_submission",
        ]

    def get_my_submission(self, obj):
        user = self.context["request"].user
        if not user.is_student:
            return None
        sub = self.context.get("submissions", {}).get(obj.id)
        if sub is None:
            return None
        return {
            "submitted_at": sub.submitted_at,
            "text_answer": sub.text_answer,
            "file_name": sub.file_name,
            "marks": sub.marks,
            "feedback": sub.feedback,
        }

    def validate_unit(self, unit):
        user = self.context["request"].user
        if user.is_lecturer and unit.lecturer_id != user.id:
            raise serializers.ValidationError("You can only set work for units you teach.")
        return unit

    def validate(self, attrs):
        current = self.instance
        text = attrs.get("allow_text", getattr(current, "allow_text", True))
        file = attrs.get("allow_file", getattr(current, "allow_file", True))
        if not (text or file):
            raise serializers.ValidationError("Allow a typed answer, a file upload, or both.")
        max_marks = attrs.get("max_marks", getattr(current, "max_marks", 100))
        if max_marks <= 0:
            raise serializers.ValidationError({"max_marks": "Maximum marks must be above zero."})
        return attrs


class StaffSubmissionSerializer(serializers.ModelSerializer):
    """What lecturers see and may change (marks and feedback only)."""

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    admission_number = serializers.CharField(source="student.admission_number", read_only=True)
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    unit_code = serializers.CharField(source="assessment.unit.code", read_only=True)
    max_marks = serializers.DecimalField(source="assessment.max_marks", max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "assessment", "assessment_title", "unit_code", "student", "student_name", "admission_number",
            "text_answer", "file_name", "file_size", "submitted_at", "max_marks", "marks", "feedback",
        ]
        read_only_fields = [
            "assessment", "student", "text_answer", "file_name", "file_size", "submitted_at",
        ]

    def validate_marks(self, value):
        if value is None:
            return value
        maximum = self.instance.assessment.max_marks
        if not 0 <= value <= maximum:
            raise serializers.ValidationError(f"Marks must be between 0 and {maximum}.")
        return value


class ExamSlotSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)

    class Meta:
        model = ExamSlot
        fields = ["id", "unit", "unit_code", "unit_title", "trimester", "date", "start_time", "end_time", "venue"]

    def validate(self, attrs):
        current = self.instance
        start = attrs.get("start_time", getattr(current, "start_time", None))
        end = attrs.get("end_time", getattr(current, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs
