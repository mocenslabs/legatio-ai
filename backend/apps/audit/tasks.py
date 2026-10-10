"""
Celery tasks for audit chain verification.

Source: 04-BUSINESS-FLOW.md Section 13.2
"""

import logging
from typing import Any
from uuid import UUID

from apps.audit.services import create_audit_event
from apps.audit.verification import (
    detect_missing_events,
    verify_full_chain,
)
from celery import shared_task
from core.enums import ActorType, EventType

logger = logging.getLogger("legatio.audit.tasks")

# Placeholder UUID for system-level audit chain events
AUDIT_CHAIN_ENTITY_ID = UUID("00000000-0000-0000-0000-000000000000")


@shared_task(name="audit.verify_chain_daily")  # type: ignore[misc]
def verify_chain_daily_task() -> dict[str, Any]:
    """
    Daily task to verify the integrity of the audit hash chain.
    Runs every day at 2:00 AM UTC via Celery Beat.
    """
    logger.info("Starting daily audit chain verification")

    result = verify_full_chain()
    missing = detect_missing_events()

    if result.is_valid and not missing:
        create_audit_event(
            event_type=EventType.SYSTEM_INTEGRITY_CHECK_PASSED,
            actor_type=ActorType.SYSTEM,
            entity_type="AuditChain",
            entity_id=AUDIT_CHAIN_ENTITY_ID,
            payload={
                "total_events": result.total_events,
                "verified_events": result.verified_events,
                "missing_events": [],
                "status": "PASSED",
            },
        )
        logger.info(
            f"Audit chain verification PASSED: "
            f"{result.verified_events}/{result.total_events} events"
        )
        return {
            "status": "PASSED",
            "total_events": result.total_events,
            "verified_events": result.verified_events,
            "missing_events": [],
        }

    error_msg = result.error_message or "Unknown error"
    if missing:
        error_msg += f"; Missing events: {missing}"

    create_audit_event(
        event_type=EventType.SYSTEM_INTEGRITY_CHECK_FAILED,
        actor_type=ActorType.SYSTEM,
        entity_type="AuditChain",
        entity_id=AUDIT_CHAIN_ENTITY_ID,
        payload={
            "total_events": result.total_events,
            "verified_events": result.verified_events,
            "missing_events": missing,
            "first_invalid_sequence": result.first_invalid_sequence,
            "error_message": error_msg,
            "status": "FAILED",
        },
    )
    logger.error(f"Audit chain verification FAILED: {error_msg}")

    return {
        "status": "FAILED",
        "total_events": result.total_events,
        "verified_events": result.verified_events,
        "missing_events": missing,
        "first_invalid_sequence": result.first_invalid_sequence,
        "error_message": error_msg,
    }
