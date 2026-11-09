from django.contrib import admin

from .models import Announcement, Enrollment, Facility, PendingRegistration, Result, TimetableSlot, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "credits", "lecturer"]
    search_fields = ["code", "title"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "unit", "trimester", "registered_at"]
    list_filter = ["trimester"]
    search_fields = ["student__email", "unit__code"]


@admin.register(PendingRegistration)
class PendingRegistrationAdmin(admin.ModelAdmin):
    list_display = ["email", "unit", "trimester", "created_at"]
    list_filter = ["trimester"]
    search_fields = ["email", "unit__code"]


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ["unit", "day", "start_time", "end_time", "venue"]
    list_filter = ["day"]


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ["student", "unit", "cat_mark", "exam_mark", "total", "grade", "academic_year"]
    search_fields = ["student__email", "unit__code"]
    list_filter = ["academic_year"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "audience", "pinned", "author", "created_at"]
    list_filter = ["audience", "pinned"]
    search_fields = ["title", "body"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "location", "opening_hours"]
    list_filter = ["category"]
    search_fields = ["name", "location"]
