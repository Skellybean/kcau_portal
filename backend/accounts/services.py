import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction

from .models import CodePurpose, EmailCode

PURPOSE_TEXT = {
    CodePurpose.VERIFY: ("Verify your KCA Virtual Campus account", "verify your email address"),
    CodePurpose.RESET: ("Reset your KCA Virtual Campus password", "reset your password"),
}


def issue_code(user, purpose):
    """Invalidate older codes, create a new one and email it to the user."""
    code = f"{secrets.randbelow(10**6):06d}"
    with transaction.atomic():
        EmailCode.objects.filter(user=user, purpose=purpose, used=False).update(used=True)
        EmailCode.objects.create(
            user=user,
            purpose=purpose,
            code_hash=make_password(code),
            expires_at=EmailCode.default_expiry(),
        )
    subject, action = PURPOSE_TEXT[purpose]
    body = (
        f"Hello {user.full_name},\n\n"
        f"Use this code to {action}: {code}\n\n"
        f"It expires in {settings.VERIFICATION_CODE_TTL_MINUTES} minutes. "
        "If you did not request it, you can ignore this message.\n\n"
        "KCA Virtual Campus"
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])


def check_code(user, purpose, submitted):
    """Return True and consume the code if it matches; count failed attempts."""
    code = (
        EmailCode.objects.filter(user=user, purpose=purpose, used=False)
        .order_by("-created_at")
        .first()
    )
    if code is None or not code.is_usable:
        return False
    if check_password(str(submitted).strip(), code.code_hash):
        code.used = True
        code.save(update_fields=["used"])
        return True
    code.attempts += 1
    code.save(update_fields=["attempts"])
    return False
