"""
Integration tests for hash chain integrity.
Verifies that the hash chain remains valid across multiple events
and detects tampering.
Source: 03-DATA-MODEL.md Section 13.1
"""

from uuid import uuid4

import pytest

from apps.audit.hash_chain import verify_hash_chain
from apps.audit.models import AuditEvent
from apps.audit.services import create_audit_event
from core.enums import ActorType, EventType


@pytest.mark.django_db
class TestHashChainIntegrity:
    def test_long_chain_integrity(self) -> None:
        """Hash chain remains valid across many events."""
        events = []
        for i in range(20):
            event = create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=uuid4(),
                entity_type="User",
                entity_id=uuid4(),
                payload={"iteration": i},
            )
            events.append(event)
        is_valid, error = verify_hash_chain(events)
        assert is_valid is True
        assert error is None

    def test_tampering_detected_at_any_point(self) -> None:
        """Tampering at any point is detected."""
        events = []
        for _ in range(10):
            event = create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=uuid4(),
                entity_type="User",
                entity_id=uuid4(),
            )
            events.append(event)

        # Tamper with event at position 5 IN MEMORY (don't persist to DB)
        tampered_index = 5
        events[tampered_index].event_type = "tampered"

        is_valid, error = verify_hash_chain(events)
        assert is_valid is False
        assert error is not None

    def test_sequence_continuity(self) -> None:
        """Sequence numbers are continuous."""
        events = []
        for _ in range(10):
            event = create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=uuid4(),
                entity_type="User",
                entity_id=uuid4(),
            )
            events.append(event)
        for i, event in enumerate(events):
            assert event.sequence_number == i + 1

    def test_genesis_event_has_no_previous_hash(self) -> None:
        """First event has no previous_event_hash."""
        first_event = AuditEvent.objects.order_by("sequence_number").first()
        if first_event and first_event.sequence_number == 1:
            assert first_event.previous_event_hash in (None, "")

    def test_all_subsequent_events_have_previous_hash(self) -> None:
        """All events after the first have a previous_event_hash."""
        events = list(AuditEvent.objects.order_by("sequence_number"))
        if len(events) > 1:
            for event in events[1:]:
                assert event.previous_event_hash is not None
                assert len(event.previous_event_hash) == 64
