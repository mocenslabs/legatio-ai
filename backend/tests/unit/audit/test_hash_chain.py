"""
Unit tests for hash chain computation.
Source: 03-DATA-MODEL.md Section 13.1
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.audit.hash_chain import (
    compute_event_hash,
    compute_payload_hash,
    verify_event_hash,
    verify_hash_chain,
)
from apps.audit.services import create_audit_event
from core.enums import ActorType, EventType


class TestComputePayloadHash:
    def test_deterministic(self) -> None:
        """Same payload produces same hash."""
        payload = {"key": "value"}
        hash1 = compute_payload_hash(payload)
        hash2 = compute_payload_hash(payload)
        assert hash1 == hash2

    def test_different_payloads_different_hashes(self) -> None:
        """Different payloads produce different hashes."""
        hash1 = compute_payload_hash({"key": "value1"})
        hash2 = compute_payload_hash({"key": "value2"})
        assert hash1 != hash2

    def test_key_order_irrelevant(self) -> None:
        """Key order doesn't affect hash (canonical JSON)."""
        hash1 = compute_payload_hash({"a": 1, "b": 2})
        hash2 = compute_payload_hash({"b": 2, "a": 1})
        assert hash1 == hash2

    def test_empty_payload(self) -> None:
        """Empty payload produces valid hash."""
        hash1 = compute_payload_hash({})
        assert len(hash1) == 64  # SHA-256 hex length


class TestComputeEventHash:
    def test_deterministic(self) -> None:
        """Same inputs produce same hash."""
        created_at = datetime.now(UTC)
        entity_id = uuid4()
        actor_id = uuid4()
        hash1 = compute_event_hash(
            sequence_number=1,
            created_at=created_at,
            event_type="user.registered",
            actor_type="USER",
            actor_id=actor_id,
            entity_type="User",
            entity_id=entity_id,
            previous_event_hash=None,
            payload_hash="abc123",
        )
        hash2 = compute_event_hash(
            sequence_number=1,
            created_at=created_at,
            event_type="user.registered",
            actor_type="USER",
            actor_id=actor_id,
            entity_type="User",
            entity_id=entity_id,
            previous_event_hash=None,
            payload_hash="abc123",
        )
        assert hash1 == hash2

    def test_different_inputs_different_hashes(self) -> None:
        """Different inputs produce different hashes."""
        created_at = datetime.now(UTC)
        entity_id = uuid4()
        hash1 = compute_event_hash(
            sequence_number=1,
            created_at=created_at,
            event_type="user.registered",
            actor_type="USER",
            actor_id=uuid4(),
            entity_type="User",
            entity_id=entity_id,
            previous_event_hash=None,
            payload_hash="abc123",
        )
        hash2 = compute_event_hash(
            sequence_number=2,  # Different
            created_at=created_at,
            event_type="user.registered",
            actor_type="USER",
            actor_id=uuid4(),
            entity_type="User",
            entity_id=entity_id,
            previous_event_hash=None,
            payload_hash="abc123",
        )
        assert hash1 != hash2


@pytest.mark.django_db
class TestVerifyEventHash:
    def test_valid_event(self) -> None:
        """Valid event passes verification."""
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )
        assert verify_event_hash(event) is True

    def test_tampered_event_fails(self) -> None:
        """Tampered event fails verification."""
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=uuid4(),
            entity_type="User",
            entity_id=uuid4(),
        )
        # Tamper with the event IN MEMORY (don't persist to DB)
        # This simulates what would happen if someone modified the DB directly
        event.event_type = "tampered"
        assert verify_event_hash(event) is False


@pytest.mark.django_db
class TestVerifyHashChain:
    def test_valid_chain(self) -> None:
        """Valid hash chain passes verification."""
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
        is_valid, error = verify_hash_chain(events)
        assert is_valid is True
        assert error is None

    def test_empty_chain(self) -> None:
        """Empty chain is valid."""
        is_valid, error = verify_hash_chain([])
        assert is_valid is True
        assert error is None

    def test_broken_chain_detected(self) -> None:
        """Broken chain is detected."""
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
        # Tamper with middle event IN MEMORY (don't persist to DB)
        # Change previous_event_hash to break the chain
        events[1].previous_event_hash = "tampered_hash_value"
        is_valid, error = verify_hash_chain(events)
        assert is_valid is False
        # Use (error or "") to safely handle None
        assert "Hash chain broken" in (error or "")
