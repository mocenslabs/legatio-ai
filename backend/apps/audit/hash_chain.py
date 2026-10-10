"""
Hash chain computation for AuditEvent.

Implements the cryptographic hash chain that ensures audit integrity.
Each event references the hash of the previous event, creating a
tamper-evident chain.

Source: 03-DATA-MODEL.md Section 13.1
Source: 04-BUSINESS-FLOW.md Section 13.2
"""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of the audit event payload.

    The payload is serialized to canonical JSON (sorted keys, no whitespace)
    before hashing to ensure determinism.

    Args:
        payload: The event payload dictionary.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    # Canonical JSON: sorted keys, no whitespace
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_event_hash(
    *,
    sequence_number: int,
    created_at: datetime,
    event_type: str,
    actor_type: str,
    actor_id: UUID | None,
    entity_type: str,
    entity_id: UUID,
    previous_event_hash: str | None,
    payload_hash: str,
) -> str:
    """
    Compute the hash chain value for an audit event.

    The hash is computed from a deterministic string representation of all
    relevant fields, ensuring that any modification to the event data
    will invalidate the hash chain.

    Formula (from 03-DATA-MODEL.md §13.1):
        event_hash = sha256(
            f"{sequence_number}|{created_at.isoformat()}|{event_type}|"
            f"{actor_type}|{actor_id}|{entity_type}|{entity_id}|"
            f"{previous_event_hash}|{payload_hash}"
        ).hexdigest()

    Args:
        sequence_number: Global ordering number.
        created_at: Timestamp of the event.
        event_type: Type of event (e.g., "proposal.evaluated").
        actor_type: Type of actor (USER, AGENT, SYSTEM, etc.).
        actor_id: UUID of the actor (None for system events).
        entity_type: Type of entity being audited.
        entity_id: UUID of the entity.
        previous_event_hash: Hash of the previous event (None for genesis).
        payload_hash: Hash of the event payload.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    # Build the deterministic string
    hash_input = (
        f"{sequence_number}|"
        f"{created_at.isoformat()}|"
        f"{event_type}|"
        f"{actor_type}|"
        f"{actor_id or ''}|"
        f"{entity_type}|"
        f"{entity_id}|"
        f"{previous_event_hash or ''}|"
        f"{payload_hash}"
    )

    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def verify_event_hash(event: Any) -> bool:
    """
    Verify that an event's hash matches its computed hash.

    Args:
        event: AuditEvent instance.

    Returns:
        True if the hash is valid, False otherwise.
    """
    computed = compute_event_hash(
        sequence_number=event.sequence_number,
        created_at=event.created_at,
        event_type=event.event_type,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        previous_event_hash=event.previous_event_hash,
        payload_hash=event.payload_hash,
    )
    return bool(computed == event.event_hash)


def verify_hash_chain(events: list[Any]) -> tuple[bool, str | None]:
    """
    Verify the integrity of a hash chain.

    Checks that:
    1. Each event's hash is valid.
    2. Each event's previous_event_hash matches the previous event's event_hash.
    3. Events are in sequence order.

    Args:
        events: List of AuditEvent instances in sequence order.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    if not events:
        return True, None

    # Check first event
    first = events[0]
    if first.sequence_number != 1:
        return False, f"First event has sequence_number {first.sequence_number}, expected 1"

    if first.previous_event_hash is not None:
        return False, "First event should have previous_event_hash=None"

    if not verify_event_hash(first):
        return False, f"Event {first.sequence_number} has invalid hash"

    # Check subsequent events
    for i in range(1, len(events)):
        current = events[i]
        previous = events[i - 1]

        # Check sequence continuity
        if current.sequence_number != previous.sequence_number + 1:
            return (
                False,
                f"Sequence gap: event {previous.sequence_number} → {current.sequence_number}",
            )

        # Check hash chain continuity
        if current.previous_event_hash != previous.event_hash:
            return (
                False,
                f"Hash chain broken at event {current.sequence_number}: "
                f"previous_event_hash mismatch",
            )

        # Check event hash validity
        if not verify_event_hash(current):
            return False, f"Event {current.sequence_number} has invalid hash"

    return True, None
