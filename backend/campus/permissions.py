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
