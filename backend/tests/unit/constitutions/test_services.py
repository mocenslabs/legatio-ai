"""Unit tests for Constitution service layer."""

from __future__ import annotations

import pytest

from apps.accounts.models import User
from apps.constitutions.models import Constitution
from apps.constitutions.services import ConstitutionService, ConstitutionServiceError


@pytest.mark.django_db
class TestConstitutionService:
    def test_get_active_constitutions(self) -> None:
        """Verify only active constitutions are returned."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        Constitution.objects.create(user=user, name="Active", is_active=True)
        Constitution.objects.create(user=user, name="Inactive", is_active=False)

        active = ConstitutionService.get_active_constitutions(user)
        assert active.count() == 1
        assert active.first().name == "Active"  # type: ignore

    def test_create_constitution(self) -> None:
        """Verify constitution creation via service."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        constitution = ConstitutionService.create_constitution(
            user=user,
            name="Service Constitution",
            description="Created via service",
        )
        assert constitution.name == "Service Constitution"
        assert constitution.user == user

    def test_create_constitution_duplicate_name(self) -> None:
        """Verify service prevents duplicate names for same user."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        ConstitutionService.create_constitution(user=user, name="Duplicate")

        with pytest.raises(ConstitutionServiceError):
            ConstitutionService.create_constitution(user=user, name="Duplicate")

    def test_deactivate_constitution(self) -> None:
        """Verify constitution can be deactivated."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        constitution = Constitution.objects.create(user=user, name="To Deactivate")

        updated = ConstitutionService.deactivate_constitution(constitution.id, user)
        assert updated.is_active is False

        # Verify in DB
        constitution.refresh_from_db()
        assert constitution.is_active is False
