from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission

FEES_MESSAGE = {
    "code": "fees_outstanding",
    "detail": "Your school fees are not cleared, so the Virtual Campus is locked. Clear your fees and try again.",
}


def fees_cleared(user):
    """True when the user may use the campus: staff always, students only with cleared fees.

    A student with no fee record counts as not cleared. Set FEE_GATE_ENABLED=0 to switch the gate off.
    """
    if not getattr(settings, "FEE_GATE_ENABLED", True):
        return True
    if not user.is_authenticated or not user.is_student:
        return True
    from .models import FeeStatus

    return FeeStatus.objects.filter(email__iexact=user.email, cleared=True).exists()


class FeesCleared(BasePermission):
    """Blocks students whose fees are outstanding. Added to every API view by default."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if fees_cleared(request.user):
            return True
        self.message = FEES_MESSAGE
        return False


class _FeeAware(BasePermission):
    def fees_ok(self, request):
        if fees_cleared(request.user):
            return True
        self.message = FEES_MESSAGE
        return False


class IsAdminRoleOrReadOnly(_FeeAware):
    """Everyone signed in can read; only administrators can change."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not self.fees_ok(request):
            return False
        return request.method in SAFE_METHODS or request.user.is_admin_role


class IsStaffRoleOrReadOnly(_FeeAware):
    """Everyone signed in can read; lecturers and administrators can change."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not self.fees_ok(request):
            return False
        return request.method in SAFE_METHODS or request.user.is_staff_role


class IsStaffRole(_FeeAware):
    """Lecturers and administrators only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff_role


class TimetablePermission(_FeeAware):
    """Everyone signed in can read. Administrators change everything.
    A lecturer may only update slots of units they teach (the serializer limits which fields)."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not self.fees_ok(request):
            return False
        if request.method in SAFE_METHODS or user.is_admin_role:
            return True
        return user.is_lecturer and view.action in ("update", "partial_update")

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS or user.is_admin_role:
            return True
        return user.is_lecturer and obj.unit.lecturer_id == user.id
