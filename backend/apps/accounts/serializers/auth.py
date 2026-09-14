"""Authentication serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import User


class RegisterSerializer(serializers.ModelSerializer[User]):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate(self, data: dict) -> dict:
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict) -> dict:
        email = data.get("email")
        password = data.get("password")

        if not password:
            raise serializers.ValidationError("Password is required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as e:
            raise serializers.ValidationError("Invalid credentials.") from e

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data["user"] = user
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh."""

    refresh = serializers.CharField()


class TwoFactorEnableSerializer(serializers.Serializer):
    """Serializer for enabling 2FA."""

    pass


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA code."""

    code = serializers.CharField(max_length=6, min_length=6)

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("Code must be numeric.")
        return value
