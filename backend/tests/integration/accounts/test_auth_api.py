"""Integration tests for authentication API endpoints."""

import pyotp
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import (
    generate_access_token,
    generate_refresh_token,
    register_user,
)
from apps.accounts.services.totp import confirm_2fa_setup, enable_2fa

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPI:
    def test_register_success(self) -> None:
        client = APIClient()
        response = client.post(
            "/api/v1/auth/register/",
            {
                "email": "test@example.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == "test@example.com"

    def test_register_duplicate_email(self) -> None:
        register_user(email="test@example.com", password="testpass123")
        client = APIClient()
        response = client.post(
            "/api/v1/auth/register/",
            {"email": "test@example.com", "password": "testpass456"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self) -> None:
        client = APIClient()
        response = client.post(
            "/api/v1/auth/register/",
            {"email": "test@example.com", "password": "short"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginAPI:
    def test_login_success(self) -> None:
        register_user(email="test@example.com", password="testpass123")
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self) -> None:
        register_user(email="test@example.com", password="testpass123")
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "wrongpass"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_2fa_requires_verification(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        confirm_2fa_setup(user, pyotp.TOTP(secret).now())
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["requires_2fa"] is True


@pytest.mark.django_db
class TestRefreshAPI:
    def test_refresh_success(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        refresh_token = generate_refresh_token(user)
        client = APIClient()
        response = client.post(
            "/api/v1/auth/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token(self) -> None:
        client = APIClient()
        response = client.post(
            "/api/v1/auth/refresh/",
            {"refresh": "invalid-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeAPI:
    def test_me_authenticated(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "test@example.com"

    def test_me_unauthenticated(self) -> None:
        client = APIClient()
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTwoFactorAPI:
    def test_enable_2fa(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post("/api/v1/auth/2fa/enable/", format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "secret" in response.data
        assert "uri" in response.data
        assert "qr_code_url" in response.data

    def test_confirm_2fa(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        code = pyotp.TOTP(secret).now()
        response = client.post("/api/v1/auth/2fa/confirm/", {"code": code}, format="json")
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.two_factor_enabled is True

    def test_disable_2fa(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        confirm_2fa_setup(user, pyotp.TOTP(secret).now())
        user.refresh_from_db()
        token = generate_access_token(user, totp_verified=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        code = pyotp.TOTP(user.totp_secret).now()
        response = client.post("/api/v1/auth/2fa/disable/", {"code": code}, format="json")
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.two_factor_enabled is False
