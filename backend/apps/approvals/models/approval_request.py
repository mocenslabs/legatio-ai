"""ApprovalRequest model definition.

This module defines the ApprovalRequest model, which represents an individual
human approval request generated when the policy engine requires human approval
for a proposed action.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ApprovalStatus(models.TextChoices):
    """Status lifecycle of an approval request."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class ApprovalRequest(models.Model):
    """A human approval request for a proposal.

    Generated automatically when the policy engine returns
    REQUIRE_HUMAN_APPROVAL. Each required approver/role gets an
    individual request that must be resolved before execution.

    Attributes:
        id: UUID primary key.
        proposal: The proposal requiring approval.
        required_role: The role authorized to approve (e.g., 'manager').
        assigned_to: Specific user assigned to approve (optional).
        status: Current approval status.
        decided_by: User who made the decision.
        decided_at: Timestamp of the decision.
        notes: Optional notes provided by the approver.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    proposal = models.ForeignKey(
        "proposals.Proposal",
        on_delete=models.CASCADE,
        related_name="approval_requests",
        verbose_name=_("Proposal"),
        help_text=_("The proposal requiring approval."),
    )
    required_role = models.CharField(
        max_length=100,
        verbose_name=_("Required Role"),
        help_text=_("The role authorized to approve this request (e.g., 'manager')."),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_approvals",
        verbose_name=_("Assigned To"),
        help_text=_("Specific user assigned to approve this request."),
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        verbose_name=_("Status"),
        help_text=_("Current status of the approval request."),
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_approvals",
        verbose_name=_("Decided By"),
        help_text=_("User who made the approval decision."),
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Decided At"),
        help_text=_("Timestamp of the decision."),
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Notes"),
        help_text=_("Optional notes provided by the approver."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )

    class Meta:
        verbose_name = _("Approval Request")
        verbose_name_plural = _("Approval Requests")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["proposal", "status"]),
            models.Index(fields=["required_role", "status"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the approval request."""
        return f"Approval for '{self.proposal_id}' by role '{self.required_role}' ({self.status})"

    @property
    def is_pending(self) -> bool:
        """Check if the approval request is still pending.

        Returns:
            True if the request is pending a decision.
        """
        return bool(self.status == ApprovalStatus.PENDING)

    @property
    def is_resolved(self) -> bool:
        """Check if the approval request has been resolved.

        Returns:
            True if the request has been approved, rejected, or cancelled.
        """
        return bool(self.status != ApprovalStatus.PENDING)
