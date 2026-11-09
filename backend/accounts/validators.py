"""KCA-only email rules.

The check is an exact match on the part after the single '@', so look-alikes
such as ``students.kcau.ac.ke.evil.com`` or ``evilkcau.ac.ke`` are rejected.
"""
from django.conf import settings
from django.core.exceptions import ValidationError

KCA_EMAIL_MESSAGE = (
    "Only KCA University email addresses can be used. "
    "Students use their students.kcau.ac.ke address; lecturers use their kcau.ac.ke address."
)


def email_domain(email):
    value = (email or "").strip().lower()
    if value.count("@") != 1:
        return None
    local, domain = value.split("@")
    if not local or not domain:
        return None
    return domain


def classify_email(email):
    """Return 'student', 'lecturer' or None for a non-KCA address."""
    domain = email_domain(email)
    if domain is None:
        return None
    if domain in settings.KCA_STUDENT_EMAIL_DOMAINS:
        return "student"
    if domain in settings.KCA_STAFF_EMAIL_DOMAINS:
        return "lecturer"
    return None


def is_kca_email(email):
    return classify_email(email) is not None


def validate_kca_email(value):
    if not is_kca_email(value):
        raise ValidationError(KCA_EMAIL_MESSAGE, code="not_kca_email")
