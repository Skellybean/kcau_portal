from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, views_coursework

router = DefaultRouter()
router.register("units", views.UnitViewSet, basename="unit")
router.register("timetable", views.TimetableViewSet, basename="timetable")
router.register("results", views.ResultViewSet, basename="result")
router.register("announcements", views.AnnouncementViewSet, basename="announcement")
router.register("facilities", views.FacilityViewSet, basename="facility")
router.register("assessments", views_coursework.AssessmentViewSet, basename="assessment")
router.register("submissions", views_coursework.SubmissionViewSet, basename="submission")
router.register("exams", views_coursework.ExamSlotViewSet, basename="exam")

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view()),
    path("exam-card/", views_coursework.ExamCardView.as_view()),
    path("portal/registrations/", views.PortalRegistrationSyncView.as_view()),
    path("portal/fees/", views_coursework.PortalFeeSyncView.as_view()),
    path("", include(router.urls)),
]
