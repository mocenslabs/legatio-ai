"""
Models for the negotiations app.
Defines NegotiationRoom (with state machine) and NegotiationMessage (append-only log).
Source: 03-DATA-MODEL.md Sections 9 and 10
"""

import uuid
from typing import Any

from django.db import models

from apps.negotiations.managers import (
    AppendOnlyManager,
    NegotiationSoftDeleteManager,
)
from apps.negotiations.state_machine import (
    is_terminal,
    validate_transition,
)
from core.enums import (
    ActorType,
    NegotiationMessageType,
    NegotiationStatus,
)


class NegotiationRoom(models.Model):
    """
    A negotiation session between a user's agent and an external agent.
    Follows a state machine with defined transitions and guards.
    Uses soft delete for user-facing cleanup.
    Source: 03-DATA-MODEL.md Section 9
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user_agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        related_name="negotiations_as_user",
        help_text="The user's agent participating in the negotiation.",
    )
    external_agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        related_name="negotiations_as_external",
        help_text="The external agent participating in the negotiation.",
    )
    constitution = models.ForeignKey(
        "constitutions.Constitution",
        on_delete=models.PROTECT,
        related_name="negotiations",
        help_text="Constitution governing this negotiation.",
    )
    reference_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Human-readable reference, e.g., NEG-2026-0001.",
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Human-readable title, e.g., 'Hotel Madrid 5 nights'.",
    )
    user_instruction = models.TextField(
        blank=True,
        default="",
        help_text="Original user instruction, e.g., 'Find hotel in Madrid for 5 nights'.",
    )
    status = models.CharField(
        max_length=20,
        choices=NegotiationStatus.choices,
        default=NegotiationStatus.PENDING,
        db_index=True,
    )
    max_rounds = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of negotiation rounds (anti-loop protection).",
    )
    current_round = models.PositiveIntegerField(
        default=0,
        help_text="Current round number.",
    )
    ttl_hours = models.PositiveIntegerField(
        default=24,
        help_text="Time-to-live in hours before automatic expiration.",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    # Managers (DJ012: declared after fields, before Meta)
    objects = NegotiationSoftDeleteManager()
    all_objects = models.Manager()  # noqa: DJ012

    class Meta:
        db_table = "legatio_negotiations_negotiationroom"
        verbose_name = "negotiation room"
        verbose_name_plural = "negotiation rooms"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_agent"], name="idx_room_user_agent"),
            models.Index(fields=["status"], name="idx_room_status"),
            models.Index(fields=["reference_code"], name="idx_room_reference"),
        ]

    def __str__(self) -> str:
        return f"{self.reference_code} ({self.get_status_display()})"

    def transition_to(self, new_status: NegotiationStatus) -> None:
        """
        Transition to a new status with validation.
        Args:
            new_status: The desired new status.
        Raises:
            NegotiationStateError: If the transition is invalid.
        """
        current = NegotiationStatus(self.status)
        validate_transition(current, new_status)
        self.status = new_status.value
        # Set timestamps based on transition
        from django.utils import timezone

        now = timezone.now()
        if new_status == NegotiationStatus.IN_PROGRESS and self.started_at is None:
            self.started_at = now
        elif new_status == NegotiationStatus.COMPLETED:
            self.completed_at = now
        elif new_status == NegotiationStatus.CANCELLED:
            self.cancelled_at = now
        self.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
                "cancelled_at",
                "updated_at",
            ]
        )

    def increment_round(self) -> None:
        """Increment the current round number."""
        self.current_round += 1
        self.save(update_fields=["current_round", "updated_at"])

    @property
    def is_terminal(self) -> bool:
        """Check if the negotiation is in a terminal state."""
        return is_terminal(NegotiationStatus(self.status))

    @property
    def is_active(self) -> bool:
        """Check if the negotiation is still active (not terminal, not deleted)."""
        return not self.is_terminal and self.deleted_at is None

    def soft_delete(self) -> None:
        """Soft-delete this negotiation room."""
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])


class NegotiationMessage(models.Model):
    """
    Append-only log of messages within a negotiation room.
    Messages are never updated or deleted. They form the complete
    history of the negotiation.
    Source: 03-DATA-MODEL.md Section 10
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    room = models.ForeignKey(
        NegotiationRoom,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_type = models.CharField(
        max_length=20,
        choices=ActorType.choices,
        help_text="Type of sender (USER, AGENT, EXTERNAL_AGENT, SYSTEM).",
    )
    sender_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of the sender (agent or user). Null for system messages.",
    )
    message_type = models.CharField(
        max_length=20,
        choices=NegotiationMessageType.choices,
        default=NegotiationMessageType.TEXT,
    )
    content = models.JSONField(
        help_text="Message content. Schema varies by message_type.",
    )
    round_number = models.PositiveIntegerField(
        help_text="Round number when this message was sent.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Manager
    objects = AppendOnlyManager()

    class Meta:
        db_table = "legatio_negotiations_negotiationmessage"
        verbose_name = "negotiation message"
        verbose_name_plural = "negotiation messages"
        ordering = ["room", "round_number", "created_at"]
        indexes = [
            models.Index(
                fields=["room", "round_number"],
                name="idx_msg_room_round",
            ),
            models.Index(
                fields=["sender_type", "sender_id"],
                name="idx_msg_sender",
            ),
        ]

    def __str__(self) -> str:
        return f"Message in {self.room.reference_code} R{self.round_number} ({self.sender_type})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to prevent updates to existing messages."""
        if self.pk and not self._state.adding:
            raise RuntimeError(
                "NegotiationMessage records are append-only. " "Cannot update an existing message."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Prevent deletion of messages."""
        raise RuntimeError(
            "NegotiationMessage records are append-only. " "Cannot delete a message."
        )
