"""Unit tests for AuditLog model.

Tests cover creation, the log classmethod, and string representation.
"""

from __future__ import annotations

import uuid

import pytest

from apps.audit.models import AuditAction, AuditLog


@pytest.mark.django_db
class TestAuditLog:
    """Tests for AuditLog model."""

    def test_create_minimal(self) -> None:
        """Verify audit log can be created with minimal fields."""
        entity_id = uuid.uuid4()
        audit_log = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=entity_id,
        )

        assert audit_log.action == AuditAction.PROPOSAL_CREATED
        assert audit_log.entity_type == "Proposal"
        assert audit_log.entity_id == entity_id
        assert audit_log.actor is None
        assert audit_log.metadata == {}
        assert isinstance(audit_log.id, uuid.UUID)

    def test_create_with_all_fields(self) -> None:
        """Verify audit log can be created with all fields."""
        from apps.accounts.models import User

        user = User.objects.create_user(email="actor@example.com", password="testpass123")
        entity_id = uuid.uuid4()

        audit_log = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_APPROVED,
            entity_type="Proposal",
            entity_id=entity_id,
            actor=user,
            old_state={"status": "PENDING_APPROVAL"},
            new_state={"status": "APPROVED"},
            metadata={"reason": "All approvals granted"},
            ip_address="192.168.1.1",
            user_agent="pytest",
        )

        assert audit_log.actor == user
        assert audit_log.old_state == {"status": "PENDING_APPROVAL"}
        assert audit_log.new_state == {"status": "APPROVED"}
        assert audit_log.metadata == {"reason": "All approvals granted"}
        assert audit_log.ip_address == "192.168.1.1"

    def test_log_classmethod(self) -> None:
        """Verify the log classmethod creates an audit entry."""
        entity_id = uuid.uuid4()

        audit_log = AuditLog.log(
            action=AuditAction.PROPOSAL_EXECUTED,
            entity_type="Proposal",
            entity_id=entity_id,
            old_state={"status": "APPROVED"},
            new_state={"status": "EXECUTED"},
        )

        assert audit_log.action == AuditAction.PROPOSAL_EXECUTED
        assert audit_log.entity_id == entity_id
        assert AuditLog.objects.count() == 1

    def test_str_representation(self) -> None:
        """Verify string representation includes action and entity type."""
        audit_log = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )

        assert "PROPOSAL_CREATED" in str(audit_log)
        assert "Proposal" in str(audit_log)
        assert "System" in str(audit_log)

    def test_ordering_by_created_at_desc(self) -> None:
        """Verify audit logs are ordered by created_at descending."""
        entity_id = uuid.uuid4()
        log1 = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=entity_id,
        )
        log2 = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_SUBMITTED,
            entity_type="Proposal",
            entity_id=entity_id,
        )

        logs = list(AuditLog.objects.all())

        assert logs[0].id == log2.id
        assert logs[1].id == log1.id
