"""Unit tests for Agreement and AgreementVersion models.

Tests cover creation, properties, constraints, and string representation.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.agreements.models import Agreement, AgreementStatus, AgreementVersion


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="creator@example.com", password="testpass123")


@pytest.mark.django_db
class TestAgreement:
    """Tests for Agreement model."""

    def test_create_minimal(self, user: User) -> None:
        """Verify agreement can be created with minimal fields."""
        agreement = Agreement.objects.create(
            title="Test Agreement",
            terms={"clause": "value"},
            created_by=user,
        )

        assert agreement.title == "Test Agreement"
        assert agreement.terms == {"clause": "value"}
        assert agreement.status == AgreementStatus.DRAFT
        assert agreement.proposal is None
        assert agreement.constitution is None
        assert isinstance(agreement.id, uuid.UUID)

    def test_create_with_all_fields(self, user: User) -> None:
        """Verify agreement can be created with all fields."""
        now = timezone.now()
        agreement = Agreement.objects.create(
            title="Full Agreement",
            description="A detailed agreement",
            terms={"amount": 1000},
            status=AgreementStatus.ACTIVE,
            effective_date=now,
            expiration_date=None,
            created_by=user,
        )

        assert agreement.title == "Full Agreement"
        assert agreement.description == "A detailed agreement"
        assert agreement.status == AgreementStatus.ACTIVE
        assert agreement.effective_date == now

    def test_str_representation(self, user: User) -> None:
        """Verify string representation includes title and status."""
        agreement = Agreement.objects.create(
            title="My Agreement",
            terms={},
            created_by=user,
        )

        assert str(agreement) == "My Agreement (DRAFT)"

    def test_default_status_is_draft(self, user: User) -> None:
        """Verify default status is DRAFT."""
        agreement = Agreement.objects.create(
            title="Default Status",
            terms={},
            created_by=user,
        )

        assert agreement.status == AgreementStatus.DRAFT

    def test_is_active_true(self, user: User) -> None:
        """Verify is_active returns True when status is ACTIVE."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        assert agreement.is_active is True

    def test_is_active_false_when_draft(self, user: User) -> None:
        """Verify is_active returns False when status is DRAFT."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
        )

        assert agreement.is_active is False

    def test_is_expired_true(self, user: User) -> None:
        """Verify is_expired returns True when expiration_date has passed."""

        past = timezone.now() - timedelta(days=1)
        agreement = Agreement.objects.create(
            title="Expired Agreement",
            terms={},
            created_by=user,
            expiration_date=past,
        )

        assert agreement.is_expired is True

    def test_is_expired_false_when_no_expiration(self, user: User) -> None:
        """Verify is_expired returns False when no expiration_date set."""
        agreement = Agreement.objects.create(
            title="No Expiration",
            terms={},
            created_by=user,
        )

        assert agreement.is_expired is False

    def test_can_be_activated_true_when_draft(self, user: User) -> None:
        """Verify can_be_activated returns True when status is DRAFT."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
        )

        assert agreement.can_be_activated is True

    def test_can_be_activated_false_when_active(self, user: User) -> None:
        """Verify can_be_activated returns False when status is ACTIVE."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        assert agreement.can_be_activated is False

    def test_ordering_by_created_at_desc(self, user: User) -> None:
        """Verify agreements are ordered by created_at descending."""
        agreement1 = Agreement.objects.create(title="First", terms={}, created_by=user)
        agreement2 = Agreement.objects.create(title="Second", terms={}, created_by=user)

        agreements = list(Agreement.objects.all())

        assert agreements[0].id == agreement2.id
        assert agreements[1].id == agreement1.id


@pytest.mark.django_db
class TestAgreementVersion:
    """Tests for AgreementVersion model."""

    def test_create_minimal(self, user: User) -> None:
        """Verify version can be created with minimal fields."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)
        version = AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title=agreement.title,
            terms=agreement.terms,
            created_by=user,
        )

        assert version.agreement == agreement
        assert version.version_number == 1
        assert version.title == "Test Agreement"
        assert version.change_reason == ""

    def test_str_representation(self, user: User) -> None:
        """Verify string representation includes agreement and version number."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)
        version = AgreementVersion.objects.create(
            agreement=agreement,
            version_number=2,
            title=agreement.title,
            terms=agreement.terms,
            created_by=user,
        )

        assert "v2" in str(version)

    def test_unique_version_number_constraint(self, user: User) -> None:
        """Verify version_number is unique per agreement."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)
        AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title="V1",
            terms={},
            created_by=user,
        )

        with pytest.raises(Exception):
            AgreementVersion.objects.create(
                agreement=agreement,
                version_number=1,
                title="Duplicate",
                terms={},
                created_by=user,
            )

    def test_cascade_delete_with_agreement(self, user: User) -> None:
        """Verify versions are deleted when agreement is deleted."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)
        version = AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title=agreement.title,
            terms={},
            created_by=user,
        )
        version_id = version.id

        agreement.delete()

        assert not AgreementVersion.objects.filter(id=version_id).exists()
