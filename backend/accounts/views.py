from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CodePurpose, User
from .serializers import (
    EmailOnlySerializer,
    LoginSerializer,
    RegisterSerializer,
    ResetConfirmSerializer,
    UserSerializer,
    VerifySerializer,
)
from .services import check_code, issue_code
from .validators import classify_email

INVALID_CODE = {"detail": "That code is incorrect or has expired. Request a new one."}


def auth_payload(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key, "user": UserSerializer(user).data}


class PublicAuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"


class RegisterView(PublicAuthView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        role = classify_email(data["email"])

        with transaction.atomic():
            user = User.objects.filter(email=data["email"]).first()
            if user and user.is_verified:
                return Response(
                    {"detail": "An account with this email already exists. Sign in instead."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user is None:
                user = User(email=data["email"], role=role)
            # An unverified record is simply refreshed so a mistyped signup can be redone.
            user.full_name = data["full_name"]
            user.admission_number = data.get("admission_number", "") if role == "student" else ""
            user.set_password(data["password"])
            user.save()

        issue_code(user, CodePurpose.VERIFY)
        return Response(
            {"detail": "We sent a 6-digit code to your KCA email.", "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(PublicAuthView):
    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user is None or not check_code(user, CodePurpose.VERIFY, serializer.validated_data["code"]):
            return Response(INVALID_CODE, status=status.HTTP_400_BAD_REQUEST)
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        # Units the student already registered for on the portal appear straight away.
        from campus.sync import claim_pending

        claim_pending(user)
        return Response(auth_payload(user))


class ResendCodeView(PublicAuthView):
    throttle_scope = "code"

    def post(self, request):
        serializer = EmailOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"], is_verified=False).first()
        if user:
            issue_code(user, CodePurpose.VERIFY)
        # Same answer either way so the endpoint does not reveal which accounts exist.
        return Response({"detail": "If that account is awaiting verification, a new code was sent."})


class LoginView(PublicAuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            problems = serializer.errors.get("non_field_errors", [])
            if any(getattr(p, "code", "") == "email_not_verified" for p in problems):
                return Response(
                    {"code": "email_not_verified", "detail": "Verify your email address before signing in."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer.is_valid(raise_exception=True)
        return Response(auth_payload(serializer.validated_data["user"]))


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordResetRequestView(PublicAuthView):
    throttle_scope = "code"

    def post(self, request):
        serializer = EmailOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"], is_verified=True).first()
        if user:
            issue_code(user, CodePurpose.RESET)
        return Response({"detail": "If that account exists, a reset code was sent to it."})


class PasswordResetConfirmView(PublicAuthView):
    def post(self, request):
        serializer = ResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(email=data["email"], is_verified=True).first()
        if user is None or not check_code(user, CodePurpose.RESET, data["code"]):
            return Response(INVALID_CODE, status=status.HTTP_400_BAD_REQUEST)
        validate_password(data["new_password"], user=user)
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        return Response({"detail": "Password updated. You can sign in now."})
