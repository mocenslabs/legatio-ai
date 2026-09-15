"""Unit tests for Constitution model."""

from __future__ import annotations

import pytest
from django.db.utils import IntegrityError

from apps.accounts.models import User
from apps.constitutions.models import Constitution


@pytest.mark.django_db
class TestConstitutionModel:
    def test_create_constitution(self) -> None:
        """Verify a constitution can be created."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        constitution = Constitution.objects.create(
            user=user,
            name="Test Constitution",
            description="A test constitution",
        )
        assert constitution.name == "Test Constitution"
        assert constitution.user == user
        assert constitution.is_active is True

    def test_unique_name_per_user(self) -> None:
        """Verify constitution names must be unique per user."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        Constitution.objects.create(user=user, name="My Constitution")

        with pytest.raises(IntegrityError):
            Constitution.objects.create(user=user, name="My Constitution")

    def test_same_name_different_users(self) -> None:
        """Verify different users can have constitutions with the same name."""
        user1 = User.objects.create_user(email="user1@example.com", password="pass")
        user2 = User.objects.create_user(email="user2@example.com", password="pass")

        c1 = Constitution.objects.create(user=user1, name="Shared Name")
        c2 = Constitution.objects.create(user=user2, name="Shared Name")

        assert c1.id != c2.id
        assert c1.name == c2.name
