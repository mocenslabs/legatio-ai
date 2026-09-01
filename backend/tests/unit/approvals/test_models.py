"""Unit tests for ApprovalRequest model.

Tests cover creation, properties, and string representation.
"""

from __future__ import annotations

import pytest

from apps.accounts.models import User
from apps.approvals.models import ApprovalRequest, ApprovalStatus
from apps.proposals.models import Proposal


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="approver@example.com", password="testpass123")


@pytest.fixture
def proposal(db: None, user: User) -> Proposal:
    """Create a test proposal.

    Args:
        db: The database fixture.
        user: The user fixture.

    Returns:
        A Proposal instance.
    """
    return Proposal.objects.create(
        title="Test Proposal",
        action_type="CREATE_PROPOSAL",
        target_resource="proposals",
        created_by=user,
    )


@pytest.mark.django_db
class TestApprovalRequest:
    """Tests for ApprovalRequest model."""

    def test_create_minimal(self, proposal: Proposal) -> None:
        """Verify approval request can be created with minimal fields."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
        )

        assert approval.proposal == proposal
        assert approval.required_role == "manager"
        assert approval.status == ApprovalStatus.PENDING
        assert approval.assigned_to is None
        assert approval.decided_by is None
        assert approval.decided_at is None
        assert approval.notes == ""

    def test_default_status_is_pending(self, proposal: Proposal) -> None:
        """Verify default status is PENDING."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="director",
        )

        assert approval.status == ApprovalStatus.PENDING

    def test_str_representation(self, proposal: Proposal) -> None:
        """Verify string representation includes role and status."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
        )

        assert "manager" in str(approval)
        assert "PENDING" in str(approval)

    def test_is_pending_true(self, proposal: Proposal) -> None:
        """Verify is_pending returns True when status is PENDING."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
        )

        assert approval.is_pending is True

    def test_is_pending_false_when_resolved(self, proposal: Proposal, user: User) -> None:
        """Verify is_pending returns False when status is not PENDING."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
            status=ApprovalStatus.APPROVED,
            decided_by=user,
        )

        assert approval.is_pending is False

    def test_is_resolved_true(self, proposal: Proposal, user: User) -> None:
        """Verify is_resolved returns True when status is not PENDING."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
            status=ApprovalStatus.REJECTED,
            decided_by=user,
        )

        assert approval.is_resolved is True

    def test_is_resolved_false_when_pending(self, proposal: Proposal) -> None:
        """Verify is_resolved returns False when status is PENDING."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
        )

        assert approval.is_resolved is False

    def test_cascade_delete_with_proposal(self, proposal: Proposal) -> None:
        """Verify approval requests are deleted when proposal is deleted."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
        )
        approval_id = approval.id

        proposal.delete()

        assert not ApprovalRequest.objects.filter(id=approval_id).exists()

    def test_multiple_approvals_per_proposal(self, proposal: Proposal) -> None:
        """Verify multiple approval requests can exist per proposal."""
        ApprovalRequest.objects.create(proposal=proposal, required_role="manager")
        ApprovalRequest.objects.create(proposal=proposal, required_role="director")

        approvals = ApprovalRequest.objects.filter(proposal=proposal)

        assert approvals.count() == 2
