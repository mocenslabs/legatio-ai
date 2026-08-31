"""Proposal model definition.

This module defines the Proposal model, which represents a proposed action
that must be evaluated against the policy engine before execution.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProposalStatus(models.TextChoices):
    """Status lifecycle of a proposal."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    DENIED = "DENIED", _("Denied")
    EXECUTED = "EXECUTED", _("Executed")
    CANCELLED = "CANCELLED", _("Cancelled")


class Proposal(models.Model):
    """A proposed action that must be evaluated against policies.

    Proposals represent actions that users or agents want to perform.
    They go through policy evaluation and may require human approval
    before execution.

    Attributes:
        id: UUID primary key.
        title: Human-readable title for the proposal.
        description: Detailed description of the proposal.
        action_type: The type of action being proposed.
        target_resource: The resource the action targets.
        payload: JSON data associated with the action.
        status: Current lifecycle status.
        policy_decision: Snapshot of the policy engine decision.
        created_by: User who created the proposal.
        constitution: Optional link to a specific constitution.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Human-readable title for the proposal."),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("Detailed description of the proposal."),
    )
    action_type = models.CharField(
        max_length=100,
        verbose_name=_("Action Type"),
        help_text=_("The type of action being proposed (e.g., 'CREATE_PROPOSAL')."),
    )
    target_resource = models.CharField(
        max_length=100,
        verbose_name=_("Target Resource"),
        help_text=_("The resource or entity the action targets."),
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Payload"),
        help_text=_("Arbitrary JSON data associated with the action."),
    )
    status = models.CharField(
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Current lifecycle status of the proposal."),
    )
    policy_decision = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Policy Decision"),
        help_text=_("Snapshot of the policy engine decision."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proposals",
        verbose_name=_("Created By"),
        help_text=_("User who created the proposal."),
    )
    constitution = models.ForeignKey(
        "constitutions.Constitution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proposals",
        verbose_name=_("Constitution"),
        help_text=_("Optional link to a specific constitution."),
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
        verbose_name = _("Proposal")
        verbose_name_plural = _("Proposals")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["created_by", "status"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the proposal."""
        return f"{self.title} ({self.status})"

    @property
    def requires_approval(self) -> bool:
        """Check if the proposal requires human approval.

        Returns:
            True if the policy decision requires approval.
        """
        if self.policy_decision is None:
            return False
        return bool(self.policy_decision.get("outcome") == "REQUIRE_HUMAN_APPROVAL")

    @property
    def can_be_executed(self) -> bool:
        """Check if the proposal can be executed.

        Returns:
            True if the proposal is approved and ready for execution.
        """
        return self.status == ProposalStatus.APPROVED
