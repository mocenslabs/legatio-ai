"""
Integration tests for the daily audit verification job.

Source: 04-BUSINESS-FLOW.md Section 13.2
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from apps.audit.models import AuditEvent
from apps.audit.services import create_audit_event
from apps.audit.tasks import verify_chain_daily_task
from core.enums import ActorType, EventType

User = get_user_model()


@pytest.mark.django_db
class TestVerifyChainDailyTask:
    def test_task_passes_with_valid_chain(self) -> None:
        """Task passes when chain is valid."""
        user = User.objects.create_user(email="job@example.com", password="pass")
        for _ in range(5):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        result = verify_chain_daily_task()
        assert result["status"] == "PASSED"
        assert result["total_events"] >= 5

    def test_task_fails_with_tampered_chain(self) -> None:
        """Task fails when chain is tampered."""
        user = User.objects.create_user(email="tamper_job@example.com", password="pass")
        for _ in range(3):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )

        # Tamper with an event's payload_hash via raw SQL.
        # This breaks verify_event_hash because event_hash was computed
        # with the original payload_hash.
        events = list(AuditEvent.objects.all().order_by("sequence_number"))
        if len(events) >= 2:
            target_event = events[1]
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE legatio_audit_auditevent SET payload_hash = %s WHERE id = %s",
                    ["0" * 64, target_event.id],
                )

        result = verify_chain_daily_task()
        assert result["status"] == "FAILED"
        assert result["first_invalid_sequence"] is not None

    def test_task_creates_audit_event(self) -> None:
        """Task creates an audit event for the verification."""
        user = User.objects.create_user(email="audit_job@example.com", password="pass")
        create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="User",
            entity_id=user.id,
        )
        initial_count = AuditEvent.objects.count()
        verify_chain_daily_task()

        assert AuditEvent.objects.count() > initial_count

        verification_events = AuditEvent.objects.filter(
            event_type__in=[
                EventType.SYSTEM_INTEGRITY_CHECK_PASSED,
                EventType.SYSTEM_INTEGRITY_CHECK_FAILED,
            ]
        )
        assert verification_events.exists()
