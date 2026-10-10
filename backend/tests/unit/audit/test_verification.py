"""
Unit tests for audit chain verification services.

Source: 03-DATA-MODEL.md Section 13.1
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from apps.audit.models import AuditEvent
from apps.audit.services import create_audit_event
from apps.audit.verification import (
    detect_missing_events,
    verify_chain_range,
    verify_entity_audit_trail,
    verify_full_chain,
)
from core.enums import ActorType, EventType

User = get_user_model()


@pytest.mark.django_db
class TestVerifyFullChain:
    def test_empty_chain(self) -> None:
        """Empty chain is valid."""
        result = verify_full_chain()
        assert result.is_valid is True
        assert result.total_events == 0

    def test_valid_chain(self) -> None:
        """Valid chain passes verification."""
        user = User.objects.create_user(email="chain@example.com", password="pass")
        for _ in range(5):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        result = verify_full_chain()
        assert result.is_valid is True
        assert result.total_events >= 5
        assert result.verified_events >= 5

    def test_tampered_chain_detected(self) -> None:
        """Tampered chain is detected when payload_hash is modified."""
        user = User.objects.create_user(email="tamper@example.com", password="pass")
        for _ in range(3):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )

        # Tamper with middle event's payload_hash via raw SQL.
        # This breaks verify_event_hash because event_hash was computed
        # with the original payload_hash.
        events = list(AuditEvent.objects.all().order_by("sequence_number"))
        target_event = events[1]
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE legatio_audit_auditevent SET payload_hash = %s WHERE id = %s",
                ["0" * 64, target_event.id],  # Fake hash (64 hex chars)
            )

        result = verify_full_chain()
        assert result.is_valid is False
        assert result.first_invalid_sequence is not None


@pytest.mark.django_db
class TestVerifyChainRange:
    def test_valid_range(self) -> None:
        """Valid range passes verification."""
        user = User.objects.create_user(email="range@example.com", password="pass")
        for _ in range(10):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        events = AuditEvent.objects.filter(entity_type="User", entity_id=str(user.id)).order_by(
            "sequence_number"
        )
        if events.count() >= 5:
            start_seq = events[2].sequence_number
            end_seq = events[6].sequence_number
            result = verify_chain_range(start_seq, end_seq)
            assert result.is_valid is True
            assert result.total_events == 5

    def test_empty_range(self) -> None:
        """Empty range is valid."""
        result = verify_chain_range(99999, 999999)
        assert result.is_valid is True
        assert result.total_events == 0


@pytest.mark.django_db
class TestDetectMissingEvents:
    def test_no_missing_events(self) -> None:
        """No missing events in continuous chain."""
        user = User.objects.create_user(email="missing@example.com", password="pass")
        for _ in range(5):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        missing = detect_missing_events()
        assert missing == []

    def test_missing_events_detected(self) -> None:
        """Missing events are detected."""
        user = User.objects.create_user(email="gap@example.com", password="pass")
        for _ in range(5):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )

        events = list(AuditEvent.objects.all().order_by("sequence_number"))
        if len(events) >= 3:
            target_event = events[2]
            deleted_seq = target_event.sequence_number
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM legatio_audit_auditevent WHERE id = %s",
                    [target_event.id],
                )

            missing = detect_missing_events()
            assert deleted_seq in missing


@pytest.mark.django_db
class TestVerifyEntityAuditTrail:
    def test_valid_entity_trail(self) -> None:
        """Valid entity audit trail passes verification."""
        user = User.objects.create_user(email="entity@example.com", password="pass")
        for _ in range(3):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        result = verify_entity_audit_trail("User", str(user.id))
        assert result.is_valid is True
        assert result.total_events == 3

    def test_empty_entity_trail(self) -> None:
        """Empty entity trail is valid."""
        result = verify_entity_audit_trail("User", "00000000-0000-0000-0000-000000000000")
        assert result.is_valid is True
        assert result.total_events == 0
