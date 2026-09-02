"""Unit tests for AgreementService.

Tests cover the full agreement lifecycle including versioning,
generation from proposals, and state transitions.
"""

from __future__ import annotations

import pytest

from apps.accounts.models import User
from apps.agreements.models import Agreement, AgreementStatus, AgreementVersion
from apps.agreements.services import (
    AgreementService,
    AgreementServiceError,
    InvalidTransitionError,
)
from apps.proposals.models import Proposal, ProposalStatus


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
class TestCreateAgreement:
    """Tests for AgreementService.create_agreement."""

    def test_creates_draft_agreement(self, user: User) -> None:
        """Verify agreement is created in DRAFT status."""
        agreement = AgreementService.create_agreement(
            title="Test Agreement",
            terms={"clause": "value"},
            created_by_id=user.id,
        )

        assert agreement.title == "Test Agreement"
        assert agreement.status == AgreementStatus.DRAFT
        assert agreement.created_by_id == user.id

    def test_creates_initial_version(self, user: User) -> None:
        """Verify creating an agreement also creates version 1."""
        agreement = AgreementService.create_agreement(
            title="Test Agreement",
            terms={"clause": "value"},
            created_by_id=user.id,
        )

        version = AgreementVersion.objects.get(agreement=agreement)
        assert version.version_number == 1
        assert version.title == "Test Agreement"
        assert version.terms == {"clause": "value"}


@pytest.mark.django_db
class TestGenerateFromProposal:
    """Tests for AgreementService.generate_from_proposal."""

    def test_generates_agreement_from_executed_proposal(self, user: User) -> None:
        """Verify agreement is generated from an executed proposal."""
        proposal = Proposal.objects.create(
            title="Executed Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by=user,
            status=ProposalStatus.EXECUTED,
        )

        agreement = AgreementService.generate_from_proposal(
            proposal_id=proposal.id, actor_id=user.id
        )

        assert agreement.title == "Executed Proposal"
        assert agreement.terms == {"amount": 5000}
        assert agreement.proposal == proposal
        assert agreement.status == AgreementStatus.DRAFT

    def test_generates_initial_version(self, user: User) -> None:
        """Verify generation creates version 1."""
        proposal = Proposal.objects.create(
            title="Executed Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by=user,
            status=ProposalStatus.EXECUTED,
        )

        agreement = AgreementService.generate_from_proposal(
            proposal_id=proposal.id, actor_id=user.id
        )

        assert AgreementVersion.objects.filter(agreement=agreement).count() == 1

    def test_raises_error_for_non_executed_proposal(self, user: User) -> None:
        """Verify generating from a non-executed proposal raises error."""
        proposal = Proposal.objects.create(
            title="Draft Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        with pytest.raises(InvalidTransitionError):
            AgreementService.generate_from_proposal(proposal_id=proposal.id, actor_id=user.id)


@pytest.mark.django_db
class TestActivateAgreement:
    """Tests for AgreementService.activate_agreement."""

    def test_activates_draft_agreement(self, user: User) -> None:
        """Verify activating a draft agreement sets status to ACTIVE."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        updated = AgreementService.activate_agreement(agreement.id, actor_id=user.id)

        assert updated.status == AgreementStatus.ACTIVE
        assert updated.effective_date is not None

    def test_activates_preserves_existing_effective_date(self, user: User) -> None:
        """Verify activating preserves an existing effective_date."""
        from django.utils import timezone

        existing_date = timezone.now()
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
            effective_date=existing_date,
        )

        updated = AgreementService.activate_agreement(agreement.id, actor_id=user.id)

        assert updated.effective_date == existing_date

    def test_activate_non_draft_raises_error(self, user: User) -> None:
        """Verify activating a non-draft agreement raises error."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        with pytest.raises(InvalidTransitionError):
            AgreementService.activate_agreement(agreement.id, actor_id=user.id)


@pytest.mark.django_db
class TestAmendAgreement:
    """Tests for AgreementService.amend_agreement."""

    def test_amends_active_agreement(self, user: User) -> None:
        """Verify amending an active agreement updates terms."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={"version": 1},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        updated = AgreementService.amend_agreement(
            agreement_id=agreement.id,
            terms={"version": 2},
            change_reason="Updated terms",
            actor_id=user.id,
        )

        assert updated.terms == {"version": 2}

    def test_amend_creates_new_version(self, user: User) -> None:
        """Verify amending creates a new version."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={"version": 1},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )
        # Create initial version
        AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title=agreement.title,
            terms={"version": 1},
            created_by=user,
        )

        AgreementService.amend_agreement(
            agreement_id=agreement.id,
            terms={"version": 2},
            change_reason="Updated terms",
            actor_id=user.id,
        )

        versions = AgreementVersion.objects.filter(agreement=agreement).order_by("version_number")
        assert versions.count() == 2
        assert versions[1].version_number == 2
        assert versions[1].terms == {"version": 2}

    def test_amend_non_active_raises_error(self, user: User) -> None:
        """Verify amending a non-active agreement raises error."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        with pytest.raises(InvalidTransitionError):
            AgreementService.amend_agreement(
                agreement_id=agreement.id,
                terms={},
                change_reason="Test",
                actor_id=user.id,
            )


@pytest.mark.django_db
class TestCompleteAgreement:
    """Tests for AgreementService.complete_agreement."""

    def test_completes_active_agreement(self, user: User) -> None:
        """Verify completing an active agreement sets status to COMPLETED."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        updated = AgreementService.complete_agreement(agreement.id, actor_id=user.id)

        assert updated.status == AgreementStatus.COMPLETED

    def test_complete_draft_raises_error(self, user: User) -> None:
        """Verify completing a draft agreement raises error."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        with pytest.raises(InvalidTransitionError):
            AgreementService.complete_agreement(agreement.id, actor_id=user.id)


@pytest.mark.django_db
class TestTerminateAgreement:
    """Tests for AgreementService.terminate_agreement."""

    def test_terminates_active_agreement(self, user: User) -> None:
        """Verify terminating an active agreement sets status to TERMINATED."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        updated = AgreementService.terminate_agreement(
            agreement.id, actor_id=user.id, reason="Breach of contract"
        )

        assert updated.status == AgreementStatus.TERMINATED

    def test_terminate_draft_raises_error(self, user: User) -> None:
        """Verify terminating a draft agreement raises error."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        with pytest.raises(InvalidTransitionError):
            AgreementService.terminate_agreement(agreement.id, actor_id=user.id)

    def test_terminate_nonexistent_raises_error(self, user: User) -> None:
        """Verify terminating a nonexistent agreement raises error."""
        import uuid

        with pytest.raises(AgreementServiceError):
            AgreementService.terminate_agreement(uuid.uuid4(), actor_id=user.id)
