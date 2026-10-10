"""
Audit service for creating audit events with hash chain integrity.
Uses Redis lock to serialize event creation and prevent race conditions
in the hash chain.
Source: 04-BUSINESS-FLOW.md Section 13.2
"""

import logging
from typing import Any
from uuid import UUID

import redis
from django.conf import settings
from django.db import transaction

from apps.audit.hash_chain import compute_event_hash, compute_payload_hash
from apps.audit.models import AuditEvent
from core.constants import AUDIT_CHAIN_LOCK_KEY, AUDIT_CHAIN_LOCK_TTL_SECONDS
from core.enums import ActorType, EventType

logger = logging.getLogger("legatio.audit")

# Redis client for distributed locking
_redis_client: Any = None


def _get_redis_client() -> Any:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        redis_url = settings.CELERY_BROKER_URL
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def _get_next_sequence_number() -> int:
    """
    Get the next sequence number for an audit event.
    The Redis lock ensures this is serialized.
    """
    last_event = AuditEvent.objects.order_by("-sequence_number").first()
    if last_event is None:
        return 1
    return int(last_event.sequence_number) + 1


def create_audit_event(
    *,
    event_type: EventType | str,
    actor_type: ActorType | str,
    actor_id: UUID | None = None,
    entity_type: str,
    entity_id: UUID,
    payload: dict[str, Any] | None = None,
    room_id: UUID | None = None,
    correlation_id: UUID | None = None,
) -> AuditEvent:
    """
    Create an audit event with hash chain integrity.
    Uses Redis lock to ensure only one process can append to the audit
    chain at a time, preventing race conditions.

    Args:
        event_type: Type of event (from EventType enum).
        actor_type: Type of actor (from ActorType enum).
        actor_id: UUID of the actor (None for system events).
        entity_type: Type of entity being audited.
        entity_id: UUID of the entity.
        payload: Event-specific data (optional).
        room_id: UUID of negotiation room, if applicable (optional).
        correlation_id: Request correlation ID (optional).

    Returns:
        The created AuditEvent instance.

    Raises:
        RuntimeError: If unable to acquire Redis lock.
    """
    event_type_str = event_type.value if hasattr(event_type, "value") else str(event_type)
    actor_type_str = actor_type.value if hasattr(actor_type, "value") else str(actor_type)

    payload = payload or {}
    payload_hash = compute_payload_hash(payload)

    redis_client = _get_redis_client()
    lock = redis_client.lock(
        AUDIT_CHAIN_LOCK_KEY,
        timeout=AUDIT_CHAIN_LOCK_TTL_SECONDS,
    )

    if not lock.acquire(blocking=True, blocking_timeout=5):
        raise RuntimeError(
            "Unable to acquire audit chain lock. " "Another process is creating an audit event."
        )

    try:
        with transaction.atomic():
            previous_event_hash: str | None = None
            last_event = AuditEvent.objects.order_by("-sequence_number").first()
            if last_event is not None:
                previous_event_hash = last_event.event_hash

            sequence_number = _get_next_sequence_number()

            event = AuditEvent(
                sequence_number=sequence_number,
                event_type=event_type_str,
                actor_type=actor_type_str,
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
                payload_hash=payload_hash,
                previous_event_hash=previous_event_hash,
                event_hash="placeholder",
                room_id=room_id,
                correlation_id=correlation_id,
            )

            event._state.adding = True
            event.save()

            event_hash = compute_event_hash(
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

            # Update hash via raw SQL to bypass immutability check.
            # Safe because we are inside the Redis lock + transaction.
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE legatio_audit_auditevent SET event_hash = %s WHERE id = %s",
                    [event_hash, str(event.pk)],
                )
            event.event_hash = event_hash

            logger.info(
                "audit_event_created",
                extra={
                    "sequence_number": event.sequence_number,
                    "event_type": event.event_type,
                    "entity_type": event.entity_type,
                    "entity_id": str(event.entity_id),
                    "actor_type": event.actor_type,
                },
            )

            return event
    finally:
        lock.release()
