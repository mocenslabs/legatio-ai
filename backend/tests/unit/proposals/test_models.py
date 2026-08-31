"""Unit tests for Proposal model.

Tests cover creation, properties, and string representation.
"""

from __future__ import annotations

import uuid

import pytest

from apps.accounts.models import User
from apps.proposals.models import Proposal, ProposalStatus


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="proposer@example.com", password="testpass123")


@pytest.mark.django_db
class TestProposal:
    """Tests for Proposal model."""

    def test_create_minimal(self, user: User) -> None:
        """Verify proposal can be created with minimal fields."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        assert proposal.title == "Test Proposal"
        assert proposal.action_type == "CREATE_PROPOSAL"
        assert proposal.target_resource == "proposals"
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.payload == {}
        assert proposal.policy_decision is None
        assert isinstance(proposal.id, uuid.UUID)

    def test_create_with_all_fields(self, user: User) -> None:
        """Verify proposal can be created with all fields."""
        proposal = Proposal.objects.create(
            title="Full Proposal",
            description="A detailed proposal",
            action_type="CREATE_AGREEMENT",
            target_resource="agreements",
            payload={"amount": 5000},
            status=ProposalStatus.SUBMITTED,
            created_by=user,
        )

        assert proposal.title == "Full Proposal"
        assert proposal.description == "A detailed proposal"
        assert proposal.payload == {"amount": 5000}
        assert proposal.status == ProposalStatus.SUBMITTED

    def test_str_representation(self, user: User) -> None:
        """Verify string representation includes title and status."""
        proposal = Proposal.objects.create(
            title="My Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        assert str(proposal) == "My Proposal (DRAFT)"

    def test_default_status_is_draft(self, user: User) -> None:
        """Verify default status is DRAFT."""
        proposal = Proposal.objects.create(
            title="Default Status",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        assert proposal.status == ProposalStatus.DRAFT

    def test_requires_approval_true(self, user: User) -> None:
        """Verify requires_approval returns True when decision requires it."""
        proposal = Proposal.objects.create(
            title="Needs Approval",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            policy_decision={"outcome": "REQUIRE_HUMAN_APPROVAL"},
        )

        assert proposal.requires_approval is True

    def test_requires_approval_false_when_no_decision(self, user: User) -> None:
        """Verify requires_approval returns False when no decision exists."""
        proposal = Proposal.objects.create(
            title="No Decision",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        assert proposal.requires_approval is False

    def test_requires_approval_false_when_allowed(self, user: User) -> None:
        """Verify requires_approval returns False when decision is ALLOW."""
        proposal = Proposal.objects.create(
            title="Allowed",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            policy_decision={"outcome": "ALLOW"},
        )

        assert proposal.requires_approval is False

    def test_can_be_executed_true(self, user: User) -> None:
        """Verify can_be_executed returns True when status is APPROVED."""
        proposal = Proposal.objects.create(
            title="Approved Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.APPROVED,
        )

        assert proposal.can_be_executed is True

    def test_can_be_executed_false_when_draft(self, user: User) -> None:
        """Verify can_be_executed returns False when status is DRAFT."""
        proposal = Proposal.objects.create(
            title="Draft Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        assert proposal.can_be_executed is False

    def test_ordering_by_created_at_desc(self, user: User) -> None:
        """Verify proposals are ordered by created_at descending."""
        proposal1 = Proposal.objects.create(
            title="First",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )
        proposal2 = Proposal.objects.create(
            title="Second",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        proposals = list(Proposal.objects.all())

        assert proposals[0].id == proposal2.id
        assert proposals[1].id == proposal1.id
