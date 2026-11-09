from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("units", views.UnitViewSet, basename="unit")
router.register("timetable", views.TimetableViewSet, basename="timetable")
router.register("results", views.ResultViewSet, basename="result")
router.register("announcements", views.AnnouncementViewSet, basename="announcement")
router.register("facilities", views.FacilityViewSet, basename="facility")

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view()),
    path("portal/registrations/", views.PortalRegistrationSyncView.as_view()),
    path("", include(router.urls)),
]
