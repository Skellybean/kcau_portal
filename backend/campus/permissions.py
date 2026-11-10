from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRoleOrReadOnly(BasePermission):
    """Everyone signed in can read; only administrators can change."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.method in SAFE_METHODS or request.user.is_admin_role


class IsStaffRoleOrReadOnly(BasePermission):
    """Everyone signed in can read; lecturers and administrators can change."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.method in SAFE_METHODS or request.user.is_staff_role


class TimetablePermission(BasePermission):
    """Everyone signed in can read. Administrators change everything.
    A lecturer may only update slots of units they teach (the serializer limits which fields)."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS or user.is_admin_role:
            return True
        return user.is_lecturer and view.action in ("update", "partial_update")

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS or user.is_admin_role:
            return True
        return user.is_lecturer and obj.unit.lecturer_id == user.id
