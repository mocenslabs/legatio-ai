"""AuditLog model definition.

This module defines the AuditLog model, which records all state transitions
and significant actions in the system for compliance and debugging purposes.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditAction(models.TextChoices):
    """Types of auditable actions."""

    # Proposal actions
    PROPOSAL_CREATED = "PROPOSAL_CREATED", _("Proposal Created")
    PROPOSAL_SUBMITTED = "PROPOSAL_SUBMITTED", _("Proposal Submitted")
    PROPOSAL_APPROVED = "PROPOSAL_APPROVED", _("Proposal Approved")
    PROPOSAL_DENIED = "PROPOSAL_DENIED", _("Proposal Denied")
    PROPOSAL_EXECUTED = "PROPOSAL_EXECUTED", _("Proposal Executed")
    PROPOSAL_CANCELLED = "PROPOSAL_CANCELLED", _("Proposal Cancelled")

    # Approval actions
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED", _("Approval Requested")
    APPROVAL_APPROVED = "APPROVAL_APPROVED", _("Approval Approved")
    APPROVAL_REJECTED = "APPROVAL_REJECTED", _("Approval Rejected")
    APPROVAL_CANCELLED = "APPROVAL_CANCELLED", _("Approval Cancelled")

    # Policy actions
    POLICY_RULE_CREATED = "POLICY_RULE_CREATED", _("Policy Rule Created")
    POLICY_RULE_UPDATED = "POLICY_RULE_UPDATED", _("Policy Rule Updated")
    POLICY_RULE_DELETED = "POLICY_RULE_DELETED", _("Policy Rule Deleted")

    # Agreement actions
    AGREEMENT_CREATED = "AGREEMENT_CREATED", _("Agreement Created")
    AGREEMENT_ACTIVATED = "AGREEMENT_ACTIVATED", _("Agreement Activated")
    AGREEMENT_SUSPENDED = "AGREEMENT_SUSPENDED", _("Agreement Suspended")
    AGREEMENT_COMPLETED = "AGREEMENT_COMPLETED", _("Agreement Completed")
    AGREEMENT_TERMINATED = "AGREEMENT_TERMINATED", _("Agreement Terminated")
    AGREEMENT_AMENDED = "AGREEMENT_AMENDED", _("Agreement Amended")

    # Negotiation actions
    NEGOTIATION_CREATED = "NEGOTIATION_CREATED", _("Negotiation Created")
    NEGOTIATION_STARTED = "NEGOTIATION_STARTED", _("Negotiation Started")
    NEGOTIATION_AGREED = "NEGOTIATION_AGREED", _("Negotiation Agreed")
    NEGOTIATION_FAILED = "NEGOTIATION_FAILED", _("Negotiation Failed")
    NEGOTIATION_CANCELLED = "NEGOTIATION_CANCELLED", _("Negotiation Cancelled")

    # Offer actions
    OFFER_CREATED = "OFFER_CREATED", _("Offer Created")
    OFFER_ACCEPTED = "OFFER_ACCEPTED", _("Offer Accepted")
    OFFER_REJECTED = "OFFER_REJECTED", _("Offer Rejected")
    OFFER_WITHDRAWN = "OFFER_WITHDRAWN", _("Offer Withdrawn")

    # Comment actions
    COMMENT_ADDED = "COMMENT_ADDED", _("Comment Added")
    COMMENT_DELETED = "COMMENT_DELETED", _("Comment Deleted")


class AuditLog(models.Model):
    """Immutable audit log entry.

    Records all state transitions and significant actions in the system.
    This model is append-only and should never be updated or deleted.

    Attributes:
        id: UUID primary key.
        action: The type of action performed.
        entity_type: The model name (e.g., 'Proposal', 'ApprovalRequest').
        entity_id: The UUID of the affected entity.
        actor: The user who performed the action (nullable for system actions).
        old_state: Previous state before the transition (JSON).
        new_state: New state after the transition (JSON).
        metadata: Additional context about the action (JSON).
        ip_address: IP address of the actor (if available).
        user_agent: User agent string (if available).
        created_at: Timestamp of the action.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    action = models.CharField(
        max_length=50,
        choices=AuditAction.choices,
        verbose_name=_("Action"),
        help_text=_("The type of action performed."),
    )
    entity_type = models.CharField(
        max_length=100,
        verbose_name=_("Entity Type"),
        help_text=_("The model name of the affected entity."),
    )
    entity_id = models.UUIDField(
        verbose_name=_("Entity ID"),
        help_text=_("The UUID of the affected entity."),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("Actor"),
        help_text=_("The user who performed the action (null for system actions)."),
    )
    old_state = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Old State"),
        help_text=_("Previous state before the transition."),
    )
    new_state = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("New State"),
        help_text=_("New state after the transition."),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional context about the action."),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address of the actor."),
    )
    user_agent = models.TextField(
        blank=True,
        default="",
        verbose_name=_("User Agent"),
        help_text=_("User agent string from the request."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp of the action."),
    )

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the audit log entry."""
        actor_name = self.actor.email if self.actor else "System"
        return f"{self.action} on {self.entity_type} by {actor_name}"

    @classmethod
    def log(
        cls,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict | None = None,
        new_state: dict | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> AuditLog:
        """Create an audit log entry.

        This is the primary method for recording audit events.

        Args:
            action: The type of action (use AuditAction enum).
            entity_type: The model name (e.g., 'Proposal').
            entity_id: The UUID of the affected entity.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous state before the transition.
            new_state: New state after the transition.
            metadata: Additional context about the action.
            ip_address: IP address of the actor.
            user_agent: User agent string.

        Returns:
            The created AuditLog instance.
        """
        return cls.objects.create(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
