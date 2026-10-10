"""
Unit tests for the audit service.

Source: 04-BUSINESS-FLOW.md Section 13.2
"""

from uuid import uuid4

import pytest

from apps.audit.services import create_audit_event
from core.enums import ActorType, EventType


@pytest.mark.django_db
class TestCreateAuditEvent:
    def test_create_simple_event(self) -> None:
        """Can create a simple audit event."""
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        assert event.pk is not None
        assert event.sequence_number is not None
        assert event.event_hash is not None
        assert event.event_hash != "placeholder"

    def test_create_event_with_payload(self) -> None:
        """Can create event with payload."""
        payload = {"email": "test@example.com", "name": "Test User"}
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
            payload=payload,
        )

        assert event.payload == payload
        assert event.payload_hash is not None

    def test_create_event_with_correlation_id(self) -> None:
        """Can create event with correlation ID."""
        correlation_id = uuid4()
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
            correlation_id=correlation_id,
        )

        assert event.correlation_id == correlation_id

    def test_create_system_event(self) -> None:
        """Can create system event without actor."""
        event = create_audit_event(
            event_type=EventType.SYSTEM_POLICY_ERROR,
            actor_type=ActorType.SYSTEM,
            actor_id=None,
            entity_type="PolicyEngine",
            entity_id=uuid4(),
        )

        assert event.actor_id is None
        assert event.actor_type == ActorType.SYSTEM.value

    def test_multiple_events_have_unique_hashes(self) -> None:
        """Multiple events have unique hashes."""
        events = []
        for _ in range(5):
            event = create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=uuid4(),
                entity_type="User",
                entity_id=uuid4(),
            )
            events.append(event)

        hashes = [e.event_hash for e in events]
        assert len(hashes) == len(set(hashes))  # All unique

    def test_event_hash_is_sha256(self) -> None:
        """Event hash is a valid SHA-256 hex string."""
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )

        assert len(event.event_hash) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in event.event_hash)
