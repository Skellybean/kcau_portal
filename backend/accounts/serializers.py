from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User
from .validators import KCA_EMAIL_MESSAGE, classify_email


class KCAEmailField(serializers.EmailField):
    """Lower-cases the address and rejects anything outside KCA's domains."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data).strip().lower()
        if classify_email(value) is None:
            raise serializers.ValidationError(KCA_EMAIL_MESSAGE)
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "admission_number", "programme", "year_of_study"]
        read_only_fields = ["id", "email", "role", "admission_number"]


class RegisterSerializer(serializers.Serializer):
    email = KCAEmailField()
    full_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    admission_number = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate(self, attrs):
        probe = User(email=attrs["email"], full_name=attrs["full_name"])
        try:
            validate_password(attrs["password"], user=probe)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs


class VerifySerializer(serializers.Serializer):
    email = KCAEmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class EmailOnlySerializer(serializers.Serializer):
    email = KCAEmailField()


class LoginSerializer(serializers.Serializer):
    email = KCAEmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"), username=attrs["email"], password=attrs["password"]
        )
        if user is None:
            raise serializers.ValidationError("Incorrect email or password.", code="authorization")
        if not user.is_verified:
            raise serializers.ValidationError(
                "Verify your email address before signing in.", code="email_not_verified"
            )
        attrs["user"] = user
        return attrs


class ResetConfirmSerializer(serializers.Serializer):
    email = KCAEmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        return attrs
