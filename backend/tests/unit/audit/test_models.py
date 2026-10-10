"""
Unit tests for the AuditEvent model.

Source: 03-DATA-MODEL.md Section 13.1
"""

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.audit.services import create_audit_event
from core.enums import ActorType, EventType

User = get_user_model()


@pytest.mark.django_db
class TestAuditEventModel:
    """Tests for the AuditEvent model."""

    def test_create_audit_event(self) -> None:
        """AuditEvent can be created via service."""
        from uuid import uuid4

        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
            payload={"email": "test@example.com"},
        )

        assert event.sequence_number is not None
        assert event.event_type == EventType.USER_REGISTERED.value
        assert event.actor_type == ActorType.USER.value
        assert event.payload_hash is not None
        assert event.event_hash is not None
        assert event.previous_event_hash is None  # First event

    def test_audit_event_is_immutable_via_save(self) -> None:
        """Cannot update an existing AuditEvent via save()."""
        from uuid import uuid4

        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        event.event_type = "modified"
        with pytest.raises(RuntimeError, match="immutable"):
            event.save()

    def test_audit_event_is_immutable_via_delete(self) -> None:
        """Cannot delete an AuditEvent via delete()."""
        from uuid import uuid4

        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        with pytest.raises(RuntimeError, match="immutable"):
            event.delete()

    def test_audit_event_sequence_increments(self) -> None:
        """Each new event gets an incremented sequence_number."""
        from uuid import uuid4

        event1 = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        event2 = create_audit_event(
            event_type=EventType.AGENT_CREATED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="Agent",
            entity_id=uuid4(),
        )

        assert event2.sequence_number == event1.sequence_number + 1

    def test_audit_event_hash_chain(self) -> None:
        """Each event references the hash of the previous event."""
        from uuid import uuid4

        event1 = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        event2 = create_audit_event(
            event_type=EventType.AGENT_CREATED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="Agent",
            entity_id=uuid4(),
        )

        assert event2.previous_event_hash == event1.event_hash

    def test_audit_event_str_representation(self) -> None:
        """String representation includes sequence number and event type."""
        from uuid import uuid4

        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        assert f"#{event.sequence_number}" in str(event)
        assert EventType.USER_REGISTERED.value in str(event)

    def test_audit_event_ordering(self) -> None:
        """Events are ordered by sequence_number."""
        from uuid import uuid4

        events = []
        for _ in range(3):
            event = create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=uuid4(),
                entity_type="User",
                entity_id=uuid4(),
            )
            events.append(event)

        ordered = list(AuditEvent.objects.all())
        assert ordered == events

    def test_audit_event_payload_hash_deterministic(self) -> None:
        """Same payload produces same hash."""
        from uuid import uuid4

        payload = {"key": "value", "number": 42}

        event1 = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
            payload=payload,
        )

        event2 = create_audit_event(
            event_type=EventType.AGENT_CREATED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="Agent",
            entity_id=uuid4(),
            payload=payload,
        )

        assert event1.payload_hash == event2.payload_hash
