from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from .validators import validate_kca_email


class Role(models.TextChoices):
    STUDENT = "student", "Student"
    LECTURER = "lecturer", "Lecturer"
    ADMIN = "admin", "Administrator"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("An email address is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.ADMIN)
        extra.setdefault("is_verified", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, validators=[validate_kca_email])
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    admission_number = models.CharField(max_length=30, blank=True)
    programme = models.CharField(max_length=150, blank=True)
    year_of_study = models.PositiveSmallIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_lecturer(self):
        return self.role == Role.LECTURER

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN

    @property
    def is_staff_role(self):
        return self.role in (Role.LECTURER, Role.ADMIN)


class CodePurpose(models.TextChoices):
    VERIFY = "verify", "Email verification"
    RESET = "reset", "Password reset"


class EmailCode(models.Model):
    """A short-lived one-time code sent to a KCA inbox. Only a hash is stored."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="codes")
    purpose = models.CharField(max_length=10, choices=CodePurpose.choices)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def default_expiry(cls):
        return timezone.now() + timedelta(minutes=settings.VERIFICATION_CODE_TTL_MINUTES)

    @property
    def is_usable(self):
        return (
            not self.used
            and self.expires_at > timezone.now()
            and self.attempts < settings.VERIFICATION_MAX_ATTEMPTS
        )
