"""Unit tests for the authentication service."""

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.services.auth import (
    authenticate_user,
    generate_access_token,
    generate_refresh_token,
    refresh_access_token,
    register_user,
)
from core.exceptions import InvalidCredentialsError

User = get_user_model()


@pytest.mark.django_db
class TestRegisterUser:
    def test_register_user_success(self) -> None:
        user = register_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.check_password("testpass123")

    def test_register_user_creates_profile(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        assert hasattr(user, "profile")
        assert user.profile is not None

    def test_register_user_duplicate_email_raises(self) -> None:
        register_user(email="test@example.com", password="testpass123")
        with pytest.raises(ValueError, match="already exists"):
            register_user(email="test@example.com", password="testpass456")

    def test_register_user_email_case_insensitive(self) -> None:
        register_user(email="Test@Example.com", password="testpass123")
        with pytest.raises(ValueError):
            register_user(email="test@example.com", password="testpass456")


@pytest.mark.django_db
class TestAuthenticateUser:
    def test_authenticate_success(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        authenticated = authenticate_user("test@example.com", "testpass123")
        assert authenticated.id == user.id

    def test_authenticate_wrong_password_raises(self) -> None:
        register_user(email="test@example.com", password="testpass123")
        with pytest.raises(InvalidCredentialsError):
            authenticate_user("test@example.com", "wrongpass")

    def test_authenticate_nonexistent_user_raises(self) -> None:
        with pytest.raises(InvalidCredentialsError):
            authenticate_user("nonexistent@example.com", "testpass123")

    def test_authenticate_inactive_user_raises(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        user.is_active = False
        user.save()
        with pytest.raises(InvalidCredentialsError):
            authenticate_user("test@example.com", "testpass123")


@pytest.mark.django_db
class TestGenerateTokens:
    def test_generate_access_token(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        token = generate_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_refresh_token(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        token = generate_refresh_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_user_id(self) -> None:
        import jwt
        from django.conf import settings

        user = register_user(email="test@example.com", password="testpass123")
        token = generate_access_token(user)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        assert payload["user_id"] == str(user.id)
        assert payload["token_type"] == "access"

    def test_refresh_token_contains_user_id(self) -> None:
        import jwt
        from django.conf import settings

        user = register_user(email="test@example.com", password="testpass123")
        token = generate_refresh_token(user)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        assert payload["user_id"] == str(user.id)
        assert payload["token_type"] == "refresh"


@pytest.mark.django_db
class TestRefreshAccessToken:
    def test_refresh_success(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        refresh_token = generate_refresh_token(user)
        new_access_token, refreshed_user = refresh_access_token(refresh_token)
        assert isinstance(new_access_token, str)
        assert refreshed_user.id == user.id

    def test_refresh_with_access_token_raises(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        access_token = generate_access_token(user)
        with pytest.raises(InvalidCredentialsError, match="Token type"):
            refresh_access_token(access_token)

    def test_refresh_with_invalid_token_raises(self) -> None:
        with pytest.raises(InvalidCredentialsError):
            refresh_access_token("invalid-token")
