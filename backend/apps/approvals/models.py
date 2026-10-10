"""
Models for the approvals app.

Defines ApprovalRequest (pending human approval) and ApprovalDecision
(append-only record of human decision).

Source: 03-DATA-MODEL.md Section 11
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.approvals.managers import AppendOnlyManager
from apps.approvals.state_machine import (
    is_terminal,
    validate_transition,
)
from core.enums import ApprovalStatus


class ApprovalRequest(models.Model):
    """
    A request for human approval of a proposal.

    Created when the Policy Engine returns REQUIRE_HUMAN_APPROVAL.
    Follows a state machine with defined transitions.

    Source: 03-DATA-MODEL.md Section 11.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    proposal = models.ForeignKey(
        "proposals.Proposal",
        on_delete=models.CASCADE,
        related_name="approval_requests",
        help_text="The proposal requiring approval.",
    )
    room = models.ForeignKey(
        "negotiations.NegotiationRoom",
        on_delete=models.CASCADE,
        related_name="approval_requests",
        help_text="Denormalized for fast queries.",
    )
    requested_by = models.ForeignKey(
        "agents.Agent",
        on_delete=models.PROTECT,
        related_name="requested_approvals",
        help_text="The user's agent that requested approval.",
    )
    policy_decision = models.ForeignKey(
        "proposals.PolicyDecision",
        on_delete=models.PROTECT,
        related_name="approval_requests",
        help_text="Why approval is needed.",
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    summary = models.TextField(
        help_text="Human-readable summary of why approval is needed.",
    )
    expires_at = models.DateTimeField(
        help_text="Default: +24h from creation.",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_approvals_approvalrequest"
        verbose_name = "approval request"
        verbose_name_plural = "approval requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "expires_at"],
                name="idx_approval_status_expires",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["proposal"],
                name="uniq_approval_proposal",
                condition=models.Q(status=ApprovalStatus.PENDING),
            ),
        ]

    def __str__(self) -> str:
        return f"ApprovalRequest {self.id} ({self.get_status_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to set default expires_at if not set."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def transition_to(self, new_status: ApprovalStatus) -> None:
        """
        Transition to a new status with validation.

        Args:
            new_status: The desired new status.

        Raises:
            ApprovalStateError: If the transition is invalid.
        """
        current = ApprovalStatus(self.status)
        validate_transition(current, new_status)
        self.status = new_status.value
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_terminal(self) -> bool:
        """Check if the approval request is in a terminal state."""
        return is_terminal(ApprovalStatus(self.status))

    @property
    def is_expired(self) -> bool:
        """Check if the approval request has expired."""
        return self.expires_at < timezone.now()


class ApprovalDecision(models.Model):
    """
    Append-only record of a human's decision on an approval request.

    ApprovalDecisions are NEVER updated or deleted.

    Source: 03-DATA-MODEL.md Section 11.2
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name="decisions",
        help_text="The approval request being decided.",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approval_decisions",
        null=True,
        blank=True,
        help_text="The user who made the decision. Null for system decisions (expired).",
    )
    decision = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        help_text="APPROVED / REJECTED / MODIFIED / EXPIRED.",
    )
    modifications = models.JSONField(
        null=True,
        blank=True,
        help_text="If decision = MODIFIED, contains the modifications.",
    )
    comment = models.TextField(
        blank=True,
        default="",
        help_text="Optional user comment.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Manager
    objects = AppendOnlyManager()

    class Meta:
        db_table = "legatio_approvals_approvaldecision"
        verbose_name = "approval decision"
        verbose_name_plural = "approval decisions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ApprovalDecision {self.id} ({self.decision})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to prevent updates to existing records."""
        if self.pk and not self._state.adding:
            raise RuntimeError(
                "ApprovalDecision records are append-only. Cannot update an existing decision."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Prevent deletion of decisions."""
        raise RuntimeError("ApprovalDecision records are append-only. Cannot delete a decision.")
