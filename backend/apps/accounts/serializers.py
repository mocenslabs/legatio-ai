"""
DRF serializers for the accounts app.
Handles validation and serialization for authentication endpoints.
"""

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for user registration."""

    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=100, required=False, default="")
    last_name = serializers.CharField(max_length=100, required=False, default="")

    def validate_email(self, value: str) -> str:
        """Validate that email is not already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Create a new user."""
        from apps.accounts.services.auth import register_user

        return register_user(**validated_data)


class LoginSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate credentials."""
        from apps.accounts.services.auth import authenticate_user

        user = authenticate_user(attrs["email"], attrs["password"])
        attrs["user"] = user
        return attrs


class RefreshTokenSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for refresh token request."""

    refresh = serializers.CharField()


class TwoFactorVerifySerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for 2FA verification."""

    code = serializers.CharField(min_length=6, max_length=6)


class TwoFactorDisableSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for 2FA disable."""

    code = serializers.CharField(min_length=6, max_length=6)


class UserSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for user data."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_verified",
            "two_factor_enabled",
            "preferred_language",
            "preferred_timezone",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]


class ChangePasswordSerializer(serializers.Serializer):  # type: ignore[type-arg]
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
