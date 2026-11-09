from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailCode, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]
    list_display = ["email", "full_name", "role", "is_verified", "is_active"]
    list_filter = ["role", "is_verified", "is_active", "is_staff"]
    search_fields = ["email", "full_name", "admission_number"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "admission_number", "programme", "year_of_study")}),
        ("Access", {"fields": ("is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2", "is_verified"),
        }),
    )


@admin.register(EmailCode)
class EmailCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "purpose", "created_at", "expires_at", "attempts", "used"]
    list_filter = ["purpose", "used"]
    readonly_fields = ["user", "purpose", "code_hash", "created_at", "expires_at", "attempts", "used"]

    def has_add_permission(self, request):
        return False
