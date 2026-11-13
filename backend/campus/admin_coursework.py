from django.contrib import admin

from .models_coursework import Assessment, ExamSlot, FeeStatus, Submission


@admin.register(FeeStatus)
class FeeStatusAdmin(admin.ModelAdmin):
    list_display = ["email", "cleared", "balance", "updated_at"]
    list_editable = ["cleared"]
    list_filter = ["cleared"]
    search_fields = ["email"]


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ["title", "unit", "kind", "due_at", "max_marks", "accept_late"]
    list_filter = ["kind", "unit"]
    search_fields = ["title", "unit__code"]

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "assessment", "submitted_at", "has_file", "marks"]
    list_filter = ["assessment__unit", "assessment__kind"]
    search_fields = ["student__email", "assessment__title"]
    readonly_fields = ["assessment", "student", "text_answer", "file_name", "file_type", "file_size", "submitted_at"]
    exclude = ["file_data"]

    def get_queryset(self, request):
        return super().get_queryset(request).defer("file_data")

    @admin.display(boolean=True, description="File")
    def has_file(self, obj):
        return bool(obj.file_name)

    def has_add_permission(self, request):
        return False


@admin.register(ExamSlot)
class ExamSlotAdmin(admin.ModelAdmin):
    list_display = ["unit", "trimester", "date", "start_time", "end_time", "venue"]
    list_filter = ["trimester", "date"]
    search_fields = ["unit__code", "venue"]
