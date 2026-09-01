"""Integration tests for audit logging and notifications in ProposalService.

Tests verify that ProposalService correctly creates audit logs and
notifications during the proposal lifecycle.
"""

from __future__ import annotations

import pytest

from apps.accounts.models import User
from apps.approvals.models import ApprovalRequest
from apps.audit.models import AuditAction, AuditLog
from apps.notifications.models import Notification, NotificationType
from apps.policies.models import PolicyRule, RuleActionType
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import ProposalService


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
class TestProposalServiceAuditLogging:
    """Tests for audit logging integration in ProposalService."""

    def test_create_proposal_logs_event(self, user: User) -> None:
        """Verify creating a proposal records an audit log."""
        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={},
            created_by_id=user.id,
        )

        audit_log = AuditLog.objects.get(entity_id=proposal.id)
        assert audit_log.action == AuditAction.PROPOSAL_CREATED
        assert audit_log.actor_id == user.id

    def test_submit_allowed_logs_approved(self, user: User) -> None:
        """Verify submitting an allowed proposal logs PROPOSAL_APPROVED."""
        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={},
            created_by_id=user.id,
        )

        ProposalService.submit_proposal(proposal.id, actor_id=user.id)

        assert AuditLog.objects.filter(
            entity_id=proposal.id, action=AuditAction.PROPOSAL_APPROVED
        ).exists()

    def test_submit_denied_logs_denied(self, user: User) -> None:
        """Verify submitting a denied proposal logs PROPOSAL_DENIED."""
        PolicyRule.objects.create(
            name="Deny Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
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

        ProposalService.submit_proposal(proposal.id, actor_id=user.id)

        assert AuditLog.objects.filter(
            entity_id=proposal.id, action=AuditAction.PROPOSAL_DENIED
        ).exists()

    def test_submit_require_approval_logs_and_creates_requests(self, user: User) -> None:
        """Verify submitting a proposal requiring approval logs events."""
        PolicyRule.objects.create(
            name="Approval Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.REQUIRE_APPROVAL,
            risk_level="MEDIUM",
            requires_approval_from=["manager"],
        )
        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by_id=user.id,
        )

        ProposalService.submit_proposal(proposal.id, actor_id=user.id)

        # Proposal submission logged
        assert AuditLog.objects.filter(
            entity_id=proposal.id, action=AuditAction.PROPOSAL_SUBMITTED
        ).exists()

        # Approval request logged
        approval = ApprovalRequest.objects.get(proposal=proposal)
        assert AuditLog.objects.filter(
            entity_id=approval.id, action=AuditAction.APPROVAL_REQUESTED
        ).exists()

    def test_execute_logs_event(self, user: User) -> None:
        """Verify executing a proposal records an audit log."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.APPROVED,
        )

        ProposalService.execute_proposal(proposal.id, actor_id=user.id)

        audit_log = AuditLog.objects.get(
            entity_id=proposal.id, action=AuditAction.PROPOSAL_EXECUTED
        )
        assert audit_log.actor_id == user.id

    def test_cancel_logs_proposal_and_approvals(self, user: User) -> None:
        """Verify cancelling logs proposal and pending approvals."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        ProposalService.cancel_proposal(proposal.id, actor_id=user.id)

        assert AuditLog.objects.filter(
            entity_id=proposal.id, action=AuditAction.PROPOSAL_CANCELLED
        ).exists()
        assert AuditLog.objects.filter(
            entity_id=approval.id, action=AuditAction.APPROVAL_CANCELLED
        ).exists()


@pytest.mark.django_db
class TestProposalServiceNotifications:
    """Tests for notification integration in ProposalService."""

    def test_submit_allowed_notifies_creator(self, user: User) -> None:
        """Verify submitting an allowed proposal notifies the creator."""
        proposal = ProposalService.create_proposal(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={},
            created_by_id=user.id,
        )

        ProposalService.submit_proposal(proposal.id, actor_id=user.id)

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_APPROVED

    def test_submit_denied_notifies_creator(self, user: User) -> None:
        """Verify submitting a denied proposal notifies the creator."""
        PolicyRule.objects.create(
            name="Deny Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
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

        ProposalService.submit_proposal(proposal.id, actor_id=user.id)

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_DENIED

    def test_submit_require_approval_notifies_creator(self, user: User) -> None:
        """Verify submitting a proposal requiring approval notifies creator."""
        PolicyRule.objects.create(
            name="Approval Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
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

        ProposalService.submit_proposal(proposal.id, actor_id=user.id)

        notifications = Notification.objects.filter(recipient=user)
        approval_notifications = notifications.filter(
            notification_type=NotificationType.APPROVAL_REQUESTED
        )
        assert approval_notifications.count() == 2

    def test_execute_notifies_creator(self, user: User) -> None:
        """Verify executing a proposal notifies the creator."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.APPROVED,
        )

        ProposalService.execute_proposal(proposal.id, actor_id=user.id)

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_EXECUTED

    def test_cancel_notifies_creator(self, user: User) -> None:
        """Verify cancelling a proposal notifies the creator."""
        proposal = Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        ProposalService.cancel_proposal(proposal.id, actor_id=user.id)

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_CANCELLED
