"""Authentication service layer."""

from __future__ import annotations

import pyotp
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


class AuthServiceError(Exception):
    """Base exception for authentication service errors."""


class UserNotFoundError(AuthServiceError):
    """Raised when a user is not found."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when credentials are invalid."""


class TwoFactorAlreadyEnabledError(AuthServiceError):
    """Raised when trying to enable 2FA that's already enabled."""


class InvalidTwoFactorCodeError(AuthServiceError):
    """Raised when 2FA code is invalid."""


class AuthService:
    """Service layer for authentication operations."""

    @staticmethod
    def register_user(
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        if User.objects.filter(email=email).exists():
            raise AuthServiceError("User with this email already exists.")

        return User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    @staticmethod
    def authenticate_user(email: str, password: str) -> User:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as e:
            raise InvalidCredentialsError("Invalid credentials.") from e

        if not user.check_password(password):
            raise InvalidCredentialsError("Invalid credentials.")

        if not user.is_active:
            raise InvalidCredentialsError("User account is disabled.")

        return user

    @staticmethod
    def generate_tokens(user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),  # type: ignore[attr-defined]
            "refresh": str(refresh),
        }

    @staticmethod
    def enable_two_factor(user: User) -> dict:
        if user.two_factor_enabled:
            raise TwoFactorAlreadyEnabledError("2FA is already enabled.")

        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save(update_fields=["totp_secret"])

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Legatio AI",
        )

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
        }

    @staticmethod
    def verify_two_factor_code(user: User, code: str) -> bool:
        if not user.totp_secret:
            raise InvalidTwoFactorCodeError("2FA is not enabled for this user.")

        totp = pyotp.TOTP(user.totp_secret)

        if not totp.verify(code, valid_window=1):
            raise InvalidTwoFactorCodeError("Invalid 2FA code.")

        if not user.two_factor_enabled:
            user.two_factor_enabled = True
            user.save(update_fields=["two_factor_enabled"])

        return True
