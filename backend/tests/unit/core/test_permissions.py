"""
Unit tests for core permissions.
Verifies that permission classes work correctly.
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from core.permissions import IsAdminUser, IsOwner, IsOwnerOrReadOnly, Requires2FA

User = get_user_model()


class FakeView:
    """Fake view for testing permissions."""

    pass


class FakeOwnedObject:
    """Fake object with owner attribute."""

    def __init__(self, owner: Any) -> None:
        self.owner = owner


class FakeUserObject:
    """Fake object with user attribute."""

    def __init__(self, user: Any) -> None:
        self.user = user


@pytest.mark.django_db
class TestIsOwnerOrReadOnly:
    def test_read_allowed_for_anyone(self) -> None:
        user1 = User.objects.create_user(email="user1@example.com", password="pass")
        user2 = User.objects.create_user(email="user2@example.com", password="pass")
        obj = FakeOwnedObject(owner=user1)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user2
        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, FakeView(), obj) is True  # type: ignore[arg-type]

    def test_write_allowed_for_owner(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        obj = FakeOwnedObject(owner=user)
        factory = APIRequestFactory()
        request = factory.put("/")
        request.user = user
        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, FakeView(), obj) is True  # type: ignore[arg-type]

    def test_write_denied_for_non_owner(self) -> None:
        user1 = User.objects.create_user(email="user1@example.com", password="pass")
        user2 = User.objects.create_user(email="user2@example.com", password="pass")
        obj = FakeOwnedObject(owner=user1)
        factory = APIRequestFactory()
        request = factory.put("/")
        request.user = user2
        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, FakeView(), obj) is False  # type: ignore[arg-type]


@pytest.mark.django_db
class TestIsOwner:
    def test_owner_can_access(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        obj = FakeOwnedObject(owner=user)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        permission = IsOwner()
        assert permission.has_object_permission(request, FakeView(), obj) is True  # type: ignore[arg-type]

    def test_non_owner_cannot_access(self) -> None:
        user1 = User.objects.create_user(email="user1@example.com", password="pass")
        user2 = User.objects.create_user(email="user2@example.com", password="pass")
        obj = FakeOwnedObject(owner=user1)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user2
        permission = IsOwner()
        assert permission.has_object_permission(request, FakeView(), obj) is False  # type: ignore[arg-type]

    def test_works_with_user_attribute(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        obj = FakeUserObject(user=user)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        permission = IsOwner()
        assert permission.has_object_permission(request, FakeView(), obj) is True  # type: ignore[arg-type]


@pytest.mark.django_db
class TestIsAdminUser:
    def test_admin_allowed(self) -> None:
        user = User.objects.create_superuser(email="admin@example.com", password="pass")
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        permission = IsAdminUser()
        assert permission.has_permission(request, FakeView()) is True  # type: ignore[arg-type]

    def test_regular_user_denied(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        permission = IsAdminUser()
        assert permission.has_permission(request, FakeView()) is False  # type: ignore[arg-type]

    def test_anonymous_denied(self) -> None:
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()
        permission = IsAdminUser()
        assert permission.has_permission(request, FakeView()) is False  # type: ignore[arg-type]


@pytest.mark.django_db
class TestRequires2FA:
    def test_user_without_2fa_allowed(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        user.two_factor_enabled = False
        user.save()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        request.auth = {"totp_verified": False}
        permission = Requires2FA()
        assert permission.has_permission(request, FakeView()) is True  # type: ignore[arg-type]

    def test_user_with_2fa_and_verified_allowed(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        user.two_factor_enabled = True
        user.save()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        request.auth = {"totp_verified": True}
        permission = Requires2FA()
        assert permission.has_permission(request, FakeView()) is True  # type: ignore[arg-type]

    def test_user_with_2fa_and_not_verified_denied(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="pass")
        user.two_factor_enabled = True
        user.save()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        request.auth = {"totp_verified": False}
        permission = Requires2FA()
        assert permission.has_permission(request, FakeView()) is False  # type: ignore[arg-type]
