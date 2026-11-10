import hmac

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Announcement, Audience, Enrollment, Facility, Result, TimetableSlot, Unit
from .sync import apply_registration
from .permissions import IsAdminRoleOrReadOnly, IsStaffRoleOrReadOnly, TimetablePermission
from .serializers import (
    AnnouncementSerializer,
    FacilitySerializer,
    ResultSerializer,
    TimetableLinkSerializer,
    TimetableSlotSerializer,
    UnitSerializer,
)


def units_for(user):
    """Units in a person's own academic life this trimester."""
    if user.is_student:
        return Unit.objects.filter(
            enrollments__student=user, enrollments__trimester=settings.CURRENT_TRIMESTER
        )
    if user.is_lecturer:
        return Unit.objects.filter(lecturer=user)
    return Unit.objects.all()


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        qs = Unit.objects.select_related("lecturer")
        if self.request.query_params.get("mine") == "1":
            qs = qs.filter(pk__in=units_for(self.request.user).values("pk"))
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(title__icontains=search))
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated and user.is_student:
            context["registered_ids"] = set(
                Enrollment.objects.filter(student=user, trimester=settings.CURRENT_TRIMESTER)
                .values_list("unit_id", flat=True)
            )
        return context


class TimetableViewSet(viewsets.ModelViewSet):
    permission_classes = [TimetablePermission]

    def get_serializer_class(self):
        user = self.request.user
        if user.is_authenticated and user.is_lecturer and self.action in ("update", "partial_update"):
            return TimetableLinkSerializer
        return TimetableSlotSerializer

    def get_queryset(self):
        qs = TimetableSlot.objects.select_related("unit")
        user = self.request.user
        if not user.is_admin_role or self.request.query_params.get("mine") == "1":
            qs = qs.filter(unit__in=units_for(user))
        day = self.request.query_params.get("day")
        if day is not None and day.isdigit():
            qs = qs.filter(day=int(day))
        return qs.distinct()


class ResultViewSet(viewsets.ModelViewSet):
    serializer_class = ResultSerializer
    permission_classes = [IsStaffRoleOrReadOnly]

    def get_queryset(self):
        qs = Result.objects.select_related("student", "unit")
        user = self.request.user
        if user.is_student:
            return qs.filter(student=user)
        if user.is_lecturer:
            return qs.filter(unit__lecturer=user)
        return qs

    def _ensure_lecturer_owns(self, serializer):
        # The serializer already checks ownership; this guards partial updates too.
        user = self.request.user
        unit = serializer.validated_data.get("unit") or serializer.instance.unit
        if user.is_lecturer and unit.lecturer_id != user.id:
            raise PermissionDenied("You can only record results for units you teach.")

    def perform_create(self, serializer):
        self._ensure_lecturer_owns(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._ensure_lecturer_owns(serializer)
        serializer.save()


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsStaffRoleOrReadOnly]

    def get_queryset(self):
        qs = Announcement.objects.select_related("author")
        user = self.request.user
        if user.is_student:
            return qs.filter(audience__in=[Audience.ALL, Audience.STUDENTS])
        if user.is_lecturer:
            return qs.filter(audience__in=[Audience.ALL, Audience.LECTURERS])
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _check_owner(self, announcement):
        user = self.request.user
        if not user.is_admin_role and announcement.author_id != user.id:
            raise PermissionDenied("You can only change announcements you posted.")

    def perform_update(self, serializer):
        self._check_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_owner(instance)
        instance.delete()


class FacilityViewSet(viewsets.ModelViewSet):
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        qs = Facility.objects.all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(location__icontains=search) | Q(description__icontains=search))
        return qs


class DashboardView(APIView):
    """One call that feeds the home screen."""

    def get(self, request):
        user = request.user
        now = timezone.localtime()
        context = {"request": request}

        slots = TimetableSlot.objects.select_related("unit").filter(unit__in=units_for(user)).distinct()
        today = list(slots.filter(day=now.weekday()).order_by("start_time"))
        upcoming = next((s for s in today if s.end_time > now.time()), None)

        announcement_qs = AnnouncementViewSet()
        announcement_qs.request = request
        latest = announcement_qs.get_queryset()[:3]

        data = {
            "unit_count": units_for(user).distinct().count(),
            "today": TimetableSlotSerializer(today, many=True, context=context).data,
            "next_class": TimetableSlotSerializer(upcoming, context=context).data if upcoming else None,
            "announcements": AnnouncementSerializer(latest, many=True, context=context).data,
        }

        if user.is_student:
            results = list(Result.objects.filter(student=user).select_related("unit"))
            weighted = sum(float(r.total) * r.unit.credits for r in results)
            credits = sum(r.unit.credits for r in results)
            data["average_mark"] = round(weighted / credits, 1) if credits else None
            data["results_count"] = len(results)
        return Response(data, status=status.HTTP_200_OK)


class PortalRegistrationSyncView(APIView):
    """Called by the KCA portal when students register for or drop units.

    POST /api/portal/registrations/ with header ``X-Portal-Key`` and a body like
    {"registrations": [{"email": "...", "unit_code": "DIT 201",
                        "trimester": "2026 Trimester 3", "action": "register"}]}
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth"
    MAX_ITEMS = 1000

    def post(self, request):
        expected = settings.PORTAL_SYNC_KEY
        if not expected:
            return Response({"detail": "Portal sync is not enabled."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        supplied = request.headers.get("X-Portal-Key", "")
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            return Response({"detail": "Invalid portal key."}, status=status.HTTP_403_FORBIDDEN)

        items = request.data.get("registrations") if isinstance(request.data, dict) else None
        if not isinstance(items, list) or not items:
            return Response({"detail": "Send a non-empty 'registrations' list."}, status=status.HTTP_400_BAD_REQUEST)
        if len(items) > self.MAX_ITEMS:
            return Response({"detail": f"At most {self.MAX_ITEMS} registrations per request."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for item in items:
            item = item if isinstance(item, dict) else {}
            outcome = apply_registration(
                item.get("email"), item.get("unit_code"), item.get("trimester"), item.get("action", "register")
            )
            results.append({"email": item.get("email"), "unit_code": item.get("unit_code"), "status": outcome})
        return Response({"results": results})
