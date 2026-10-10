"""
Authentication service for Legatio AI.
Handles user registration, login, token generation, and refresh.
Source: 02-ARCHITECTURE.md Section 11.1
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

from core.exceptions import InvalidCredentialsError

User = get_user_model()


def generate_access_token(
    user: Any,
    totp_verified: bool = False,
) -> str:
    """Generate a JWT access token for a user."""
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "token_type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES),
        "iat": datetime.now(UTC),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "totp_verified": totp_verified,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def generate_refresh_token(user: Any) -> str:
    """Generate a JWT refresh token for a user."""
    payload = {
        "user_id": str(user.id),
        "token_type": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS),
        "iat": datetime.now(UTC),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def register_user(
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
) -> Any:
    """Register a new user."""
    if User.objects.filter(email__iexact=email).exists():
        raise ValueError("A user with this email already exists.")

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    from apps.accounts.models import UserProfile

    UserProfile.objects.create(user=user)
    return user


def authenticate_user(email: str, password: str) -> Any:
    """Authenticate a user with email and password."""
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        raise InvalidCredentialsError() from None

    if not user.check_password(password):
        raise InvalidCredentialsError() from None

    if not user.is_active:
        raise InvalidCredentialsError("User account is disabled.")

    return user


def refresh_access_token(refresh_token: str) -> tuple[str, Any]:
    """Refresh an access token using a refresh token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidCredentialsError("Refresh token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidCredentialsError("Invalid refresh token.") from exc

    if payload.get("token_type") != "refresh":
        raise InvalidCredentialsError("Token type must be 'refresh'.")

    try:
        user = User.objects.get(id=payload["user_id"])
    except User.DoesNotExist as exc:
        raise InvalidCredentialsError("User not found.") from exc

    if not user.is_active:
        raise InvalidCredentialsError("User account is disabled.")

    access_token = generate_access_token(user, totp_verified=False)
    return access_token, user
