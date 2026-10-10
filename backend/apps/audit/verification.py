"""
Audit chain verification services.

Source: 04-BUSINESS-FLOW.md Section 13.2
Source: 03-DATA-MODEL.md Section 13.1
"""

import logging
from dataclasses import dataclass
from typing import Any

from apps.audit.hash_chain import verify_event_hash, verify_hash_chain
from apps.audit.models import AuditEvent

logger = logging.getLogger("legatio.audit.verification")


@dataclass
class VerificationResult:
    """Result of an audit chain verification."""

    is_valid: bool
    total_events: int
    verified_events: int
    first_invalid_sequence: int | None = None
    error_message: str | None = None


def verify_full_chain() -> VerificationResult:
    """Verify the integrity of the entire audit hash chain."""
    events = list(AuditEvent.objects.all().order_by("sequence_number"))

    if not events:
        return VerificationResult(is_valid=True, total_events=0, verified_events=0)

    is_valid, error_message = verify_hash_chain(events)

    if is_valid:
        return VerificationResult(
            is_valid=True, total_events=len(events), verified_events=len(events)
        )

    first_invalid: int | None = None
    for event in events:
        if not verify_event_hash(event):
            first_invalid = event.sequence_number
            break

    return VerificationResult(
        is_valid=False,
        total_events=len(events),
        verified_events=0,
        first_invalid_sequence=first_invalid,
        error_message=error_message,
    )


def verify_chain_range(start_sequence: int, end_sequence: int) -> VerificationResult:
    """
    Verify the integrity of a specific range of audit events.

    Verifies internal chain integrity (previous_event_hash links)
    without requiring the range to start at sequence_number 1.
    """
    events = list(
        AuditEvent.objects.filter(
            sequence_number__gte=start_sequence,
            sequence_number__lte=end_sequence,
        ).order_by("sequence_number")
    )

    if not events:
        return VerificationResult(is_valid=True, total_events=0, verified_events=0)

    # Check sequence continuity within the range
    expected_seq = start_sequence
    for event in events:
        if event.sequence_number != expected_seq:
            return VerificationResult(
                is_valid=False,
                total_events=len(events),
                verified_events=0,
                first_invalid_sequence=event.sequence_number,
                error_message=f"Missing sequence number {expected_seq} in range",
            )
        expected_seq += 1

    # Verify internal chain integrity (skip first event's previous_event_hash check)
    for i in range(1, len(events)):
        current = events[i]
        previous = events[i - 1]
        if current.previous_event_hash != previous.event_hash:
            return VerificationResult(
                is_valid=False,
                total_events=len(events),
                verified_events=i,
                first_invalid_sequence=current.sequence_number,
                error_message=f"Hash chain broken at sequence {current.sequence_number}",
            )

    # Verify each event's own hash integrity (payload_hash matches payload)
    for event in events:
        if not verify_event_hash(event):
            return VerificationResult(
                is_valid=False,
                total_events=len(events),
                verified_events=0,
                first_invalid_sequence=event.sequence_number,
                error_message=f"Event hash mismatch at sequence {event.sequence_number}",
            )

    return VerificationResult(is_valid=True, total_events=len(events), verified_events=len(events))


def detect_missing_events() -> list[int]:
    """Detect gaps in the audit chain sequence numbers."""
    all_sequences = list(
        AuditEvent.objects.values_list("sequence_number", flat=True).order_by("sequence_number")
    )

    if not all_sequences:
        return []

    expected = set(range(1, max(all_sequences) + 1))
    actual = set(all_sequences)
    missing = sorted(expected - actual)

    if missing:
        logger.warning(f"Missing audit events detected: {missing}")

    return missing


def verify_entity_audit_trail(entity_type: str, entity_id: Any) -> VerificationResult:
    """Verify the audit trail for a specific entity."""
    events = list(
        AuditEvent.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
        ).order_by("sequence_number")
    )

    if not events:
        return VerificationResult(is_valid=True, total_events=0, verified_events=0)

    for event in events:
        if not verify_event_hash(event):
            return VerificationResult(
                is_valid=False,
                total_events=len(events),
                verified_events=0,
                error_message=f"Invalid hash detected for {entity_type}#{entity_id}",
            )

    return VerificationResult(is_valid=True, total_events=len(events), verified_events=len(events))
