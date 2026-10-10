"""
Integration tests for user isolation.
Verifies that users cannot access resources belonging to other users.
Source: 00-INDEX.md Section 2.5 (Aislamiento por usuario)
"""

from datetime import timedelta

import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserProfile
from apps.accounts.services.auth import generate_access_token, register_user

User = get_user_model()


@pytest.mark.django_db
class TestUserProfileIsolation:
    def test_user_can_see_own_profile(self) -> None:
        user = register_user(email="alice@example.com", password="pass1234", first_name="Alice")
        UserProfile.objects.filter(user=user).update(display_name="Alice W.")
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "alice@example.com"
        assert response.data["first_name"] == "Alice"

    def test_user_cannot_see_other_user_profile(self) -> None:
        alice = register_user(email="alice@example.com", password="pass1234")
        register_user(email="bob@example.com", password="pass1234")

        alice_token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {alice_token}")

        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "alice@example.com"


@pytest.mark.django_db
class TestAuthenticationIsolation:
    def test_token_only_works_for_its_user(self) -> None:
        alice = register_user(email="alice@example.com", password="pass1234")
        register_user(email="bob@example.com", password="pass1234")

        alice_token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {alice_token}")

        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "alice@example.com"

    def test_invalid_token_returns_401(self) -> None:
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_returns_401(self) -> None:
        user = register_user(email="user@example.com", password="pass1234")
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "token_type": "access",
            "exp": timezone.now() - timedelta(hours=1),
            "iat": timezone.now() - timedelta(hours=2),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "totp_verified": False,
        }
        expired_token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired_token}")
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_request_returns_401(self) -> None:
        client = APIClient()
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCrossUserAccess:
    def test_user_cannot_modify_other_user(self) -> None:
        alice = register_user(email="alice@example.com", password="pass1234")
        bob = register_user(email="bob@example.com", password="pass1234")
        alice_token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {alice_token}")

        _ = client.patch("/api/v1/auth/me/", {"first_name": "Hacked"})

        bob.refresh_from_db()
        assert bob.first_name != "Hacked"

    def test_multiple_users_isolated(self) -> None:
        users = []
        for i in range(5):
            user = register_user(
                email=f"user{i}@example.com", password="pass1234", first_name=f"User{i}"
            )
            users.append(user)

        for i, user in enumerate(users):
            token = generate_access_token(user)
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            response = client.get("/api/v1/auth/me/")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["email"] == f"user{i}@example.com"
            assert response.data["first_name"] == f"User{i}"


@pytest.mark.django_db
class TestOwnershipInvariants:
    def test_user_profile_belongs_to_user(self) -> None:
        user = register_user(email="user@example.com", password="pass1234")
        profile = UserProfile.objects.get(user=user)
        assert profile.user == user

    def test_user_deletion_cascades_to_profile(self) -> None:
        user = register_user(email="user@example.com", password="pass1234")
        profile_id = UserProfile.objects.get(user=user).id
        user.delete()
        assert not UserProfile.objects.filter(id=profile_id).exists()

    def test_profile_cannot_be_reassigned(self) -> None:
        user1 = register_user(email="user1@example.com", password="pass1234")
        user2 = register_user(email="user2@example.com", password="pass1234")
        profile = UserProfile.objects.get(user=user1)
        profile.user = user2

        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            profile.save()
