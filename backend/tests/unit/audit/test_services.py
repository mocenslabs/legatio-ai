"""Unit tests for AuditService.

Tests cover the typed convenience methods for recording audit events.
"""

from __future__ import annotations

import uuid

import pytest

from apps.audit.models import AuditAction, AuditLog
from apps.audit.services import AuditService


@pytest.mark.django_db
class TestAuditService:
    """Tests for AuditService class."""

    def test_log_proposal_event(self) -> None:
        """Verify proposal events are recorded correctly."""
        proposal_id = uuid.uuid4()

        AuditService.log_proposal_event(
            action=AuditAction.PROPOSAL_CREATED,
            proposal_id=proposal_id,
            new_state={"status": "DRAFT"},
        )

        audit_log = AuditLog.objects.get(entity_id=proposal_id)
        assert audit_log.action == AuditAction.PROPOSAL_CREATED
        assert audit_log.entity_type == "Proposal"
        assert audit_log.new_state == {"status": "DRAFT"}

    def test_log_proposal_event_with_actor(self) -> None:
        """Verify proposal events record the actor."""
        from apps.accounts.models import User

        user = User.objects.create_user(email="actor@example.com", password="testpass123")
        proposal_id = uuid.uuid4()

        AuditService.log_proposal_event(
            action=AuditAction.PROPOSAL_SUBMITTED,
            proposal_id=proposal_id,
            actor_id=user.id,
            old_state={"status": "DRAFT"},
            new_state={"status": "SUBMITTED"},
        )

        audit_log = AuditLog.objects.get(entity_id=proposal_id)
        assert audit_log.actor_id == user.id

    def test_log_approval_event(self) -> None:
        """Verify approval events are recorded correctly."""
        approval_id = uuid.uuid4()

        AuditService.log_approval_event(
            action=AuditAction.APPROVAL_REQUESTED,
            approval_id=approval_id,
            new_state={"status": "PENDING", "required_role": "manager"},
            metadata={"proposal_id": str(uuid.uuid4())},
        )

        audit_log = AuditLog.objects.get(entity_id=approval_id)
        assert audit_log.action == AuditAction.APPROVAL_REQUESTED
        assert audit_log.entity_type == "ApprovalRequest"

    def test_log_policy_rule_event(self) -> None:
        """Verify policy rule events are recorded correctly."""
        rule_id = uuid.uuid4()

        AuditService.log_policy_rule_event(
            action=AuditAction.POLICY_RULE_CREATED,
            rule_id=rule_id,
            new_state={"name": "Test Rule"},
        )

        audit_log = AuditLog.objects.get(entity_id=rule_id)
        assert audit_log.action == AuditAction.POLICY_RULE_CREATED
        assert audit_log.entity_type == "PolicyRule"
