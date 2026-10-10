"""
Models for the audit app.
Defines the AuditEvent model, which is the append-only, hash-chained
audit trail for all state changes in the system.
Source: 03-DATA-MODEL.md Section 13.1
"""

import uuid
from typing import Any

from django.db import models

from apps.audit.managers import ImmutableManager, ImmutableQuerySet
from core.enums import ActorType, EventType


class AuditEvent(models.Model):
    """
    Append-only, hash-chained audit event.
    Every state change in the system creates an AuditEvent. These records
    are NEVER updated or deleted. The hash chain ensures integrity:
    each event references the hash of the previous event.
    Source: 03-DATA-MODEL.md Section 13.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    sequence_number = models.BigIntegerField(
        unique=True,
        editable=False,
        db_index=True,
    )

    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        db_index=True,
    )
    actor_type = models.CharField(
        max_length=20,
        choices=ActorType.choices,
    )
    actor_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of the actor. Null for system events.",
    )

    entity_type = models.CharField(
        max_length=50,
        help_text="Type of entity being audited (e.g., 'Proposal', 'NegotiationRoom').",
    )
    entity_id = models.UUIDField(
        help_text="UUID of the entity being audited.",
    )

    room_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="UUID of the negotiation room, if applicable. Will become FK in DEL-017.",
    )

    payload = models.JSONField(
        default=dict,
        help_text="Event-specific data. May be encrypted if sensitive.",
    )
    payload_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of the canonical payload.",
    )

    # Hash chain
    # NULL is semantically correct for the genesis event (no previous event).
    previous_event_hash = models.CharField(  # noqa: DJ001
        max_length=64,
        null=True,
        blank=True,
        help_text="Hash of the previous event. Null for genesis event.",
    )

    event_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="Hash of this event. Part of the hash chain.",
    )

    correlation_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Correlation ID for request tracing.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    objects = ImmutableManager.from_queryset(ImmutableQuerySet)()

    class Meta:
        db_table = "legatio_audit_auditevent"
        verbose_name = "audit event"
        verbose_name_plural = "audit events"
        ordering = ["sequence_number"]
        get_latest_by = "sequence_number"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="idx_audit_entity"),
            models.Index(fields=["room_id", "-created_at"], name="idx_audit_room_created"),
            models.Index(fields=["event_type"], name="idx_audit_event_type"),
            models.Index(fields=["actor_type", "actor_id"], name="idx_audit_actor"),
        ]

    def __str__(self) -> str:
        return f"AuditEvent #{self.sequence_number}: {self.event_type} on {self.entity_type}#{self.entity_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and not self._state.adding:
            raise RuntimeError(
                "AuditEvent records are immutable. Cannot update an existing audit event."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise RuntimeError("AuditEvent records are immutable. Cannot delete an audit event.")
