"""Bring unit registrations from the KCA portal into the Virtual Campus."""
from accounts.models import Role, User
from accounts.validators import classify_email

from .models import Enrollment, PendingRegistration, Unit

REGISTER = "register"
DROP = "drop"


def apply_registration(email, unit_code, trimester, action=REGISTER):
    """Apply one portal registration or drop. Returns a short status string."""
    email = (email or "").strip().lower()
    unit_code = (unit_code or "").strip()
    trimester = (trimester or "").strip()
    if action not in (REGISTER, DROP):
        return "invalid_action"
    if not trimester:
        return "missing_trimester"
    if classify_email(email) != "student":
        return "not_a_student_email"
    unit = Unit.objects.filter(code__iexact=unit_code).first()
    if unit is None:
        return "unknown_unit"

    student = User.objects.filter(email=email, role=Role.STUDENT).first()
    if action == DROP:
        Enrollment.objects.filter(student=student, unit=unit, trimester=trimester).delete() if student else None
        PendingRegistration.objects.filter(email=email, unit=unit, trimester=trimester).delete()
        return "dropped"

    if student is None:
        PendingRegistration.objects.get_or_create(email=email, unit=unit, trimester=trimester)
        return "pending_until_signup"
    Enrollment.objects.get_or_create(student=student, unit=unit, trimester=trimester)
    return "registered"


def claim_pending(user):
    """Convert any waiting portal registrations once a student has verified their email."""
    if user.role != Role.STUDENT:
        return 0
    waiting = list(PendingRegistration.objects.filter(email__iexact=user.email))
    for item in waiting:
        Enrollment.objects.get_or_create(student=user, unit=item.unit, trimester=item.trimester)
        item.delete()
    return len(waiting)
