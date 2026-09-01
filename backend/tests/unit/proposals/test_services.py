"""Unit tests for ProposalService.

Tests cover the full proposal lifecycle including policy evaluation,
approval request generation, and state transitions.
"""

from __future__ import annotations

import uuid

import pytest

from apps.accounts.models import User
from apps.approvals.models import ApprovalRequest, ApprovalStatus
from apps.policies.models import PolicyRule, RuleActionType
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import InvalidTransitionError, ProposalService, ProposalServiceError


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
class TestCreateProposal:
    """Tests for ProposalService.create_proposal."""

    def test_creates_draft_proposal(self, user: User) -> None:
        """Verify proposal is created in DRAFT status."""
        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            created_by_id=user.id,
        )

        assert proposal.title == "Test Proposal"
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.created_by_id == user.id
        assert proposal.payload == {"amount": 1000}


@pytest.mark.django_db
class TestSubmitProposal:
    """Tests for ProposalService.submit_proposal."""

    def test_submit_with_no_rules_allows(self, user: User) -> None:
        """Verify submission is ALLOWED when no rules match."""
        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 500},
            created_by_id=user.id,
        )

        updated = ProposalService.submit_proposal(proposal.id)

        assert updated.status == ProposalStatus.APPROVED
        assert updated.policy_decision is not None
        assert updated.policy_decision["outcome"] == "ALLOW"

    def test_submit_with_deny_rule_denies(self, user: User) -> None:
        """Verify submission is DENIED when a deny rule matches."""
        PolicyRule.objects.create(
            name="Deny High Amount",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
        )

        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by_id=user.id,
        )

        updated = ProposalService.submit_proposal(proposal.id)

        assert updated.status == ProposalStatus.DENIED
        assert updated.policy_decision["outcome"] == "DENY"

    def test_submit_with_approval_rule_creates_requests(self, user: User) -> None:
        """Verify submission creates approval requests when required."""
        PolicyRule.objects.create(
            name="Require Approval",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.REQUIRE_APPROVAL,
            risk_level="MEDIUM",
            requires_approval_from=["manager", "director"],
        )

        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by_id=user.id,
        )

        updated = ProposalService.submit_proposal(proposal.id)

        assert updated.status == ProposalStatus.PENDING_APPROVAL
        assert updated.policy_decision["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        approvals = ApprovalRequest.objects.filter(proposal=proposal)
        assert approvals.count() == 2

        roles = {approval.required_role for approval in approvals}
        assert roles == {"manager", "director"}

    def test_submit_non_draft_raises_error(self, user: User) -> None:
        """Verify submitting a non-draft proposal raises InvalidTransitionError."""
        proposal = Proposal.objects.create(
            title="Submitted Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.SUBMITTED,
        )

        with pytest.raises(InvalidTransitionError):
            ProposalService.submit_proposal(proposal.id)

    def test_submit_nonexistent_raises_error(self) -> None:
        """Verify submitting a nonexistent proposal raises ProposalServiceError."""
        with pytest.raises(ProposalServiceError):
            ProposalService.submit_proposal(uuid.uuid4())


@pytest.mark.django_db
class TestResolveApproval:
    """Tests for ProposalService.resolve_approval."""

    def test_all_approvals_approves_proposal(self, user: User) -> None:
        """Verify all approvals approve the proposal."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )
        approval1 = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")
        approval2 = ApprovalRequest.objects.create(proposal=proposal, required_role="director")

        ProposalService.resolve_approval(approval1.id, approved=True, decided_by_id=user.id)
        ProposalService.resolve_approval(approval2.id, approved=True, decided_by_id=user.id)

        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.APPROVED

    def test_one_rejection_denies_proposal(self, user: User) -> None:
        """Verify a single rejection denies the proposal."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )
        approval1 = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")
        approval2 = ApprovalRequest.objects.create(proposal=proposal, required_role="director")

        ProposalService.resolve_approval(approval1.id, approved=True, decided_by_id=user.id)
        ProposalService.resolve_approval(approval2.id, approved=False, decided_by_id=user.id)

        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.DENIED

    def test_resolve_updates_approval_status(self, user: User) -> None:
        """Verify resolving updates the approval request status."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        updated = ProposalService.resolve_approval(
            approval.id, approved=True, decided_by_id=user.id, notes="Looks good"
        )

        assert updated.status == ApprovalStatus.APPROVED
        assert updated.decided_by_id == user.id
        assert updated.decided_at is not None
        assert updated.notes == "Looks good"

    def test_resolve_non_pending_raises_error(self, user: User) -> None:
        """Verify resolving a non-pending approval raises InvalidTransitionError."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
            status=ApprovalStatus.APPROVED,
        )

        with pytest.raises(InvalidTransitionError):
            ProposalService.resolve_approval(approval.id, approved=True, decided_by_id=user.id)


@pytest.mark.django_db
class TestExecuteProposal:
    """Tests for ProposalService.execute_proposal."""

    def test_execute_approved_proposal(self, user: User) -> None:
        """Verify executing an approved proposal transitions to EXECUTED."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.APPROVED,
        )

        updated = ProposalService.execute_proposal(proposal.id)

        assert updated.status == ProposalStatus.EXECUTED

    def test_execute_draft_raises_error(self, user: User) -> None:
        """Verify executing a draft proposal raises InvalidTransitionError."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        with pytest.raises(InvalidTransitionError):
            ProposalService.execute_proposal(proposal.id)


@pytest.mark.django_db
class TestCancelProposal:
    """Tests for ProposalService.cancel_proposal."""

    def test_cancel_pending_proposal(self, user: User) -> None:
        """Verify cancelling a pending proposal transitions to CANCELLED."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )

        updated = ProposalService.cancel_proposal(proposal.id)

        assert updated.status == ProposalStatus.CANCELLED

    def test_cancel_cancels_pending_approvals(self, user: User) -> None:
        """Verify cancelling also cancels pending approval requests."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )
        ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        ProposalService.cancel_proposal(proposal.id)

        approvals = ApprovalRequest.objects.filter(proposal=proposal)
        assert all(approval.status == ApprovalStatus.CANCELLED for approval in approvals)

    def test_cancel_executed_raises_error(self, user: User) -> None:
        """Verify cancelling an executed proposal raises InvalidTransitionError."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.EXECUTED,
        )

        with pytest.raises(InvalidTransitionError):
            ProposalService.cancel_proposal(proposal.id)
