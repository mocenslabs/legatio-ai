"""Negotiation model definition.

This module defines the Negotiation model, which represents a negotiation
process tied to a proposal, where parties exchange offers to reach an
agreement.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class NegotiationStatus(models.TextChoices):
    """Status lifecycle of a negotiation."""

    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    AGREED = "AGREED", _("Agreed")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class Negotiation(models.Model):
    """A negotiation process tied to a proposal.

    Negotiations allow parties to exchange offers and counter-offers
    to refine the terms of a proposal before finalizing an agreement.

    Attributes:
        id: UUID primary key.
        proposal: The proposal being negotiated.
        title: Human-readable title for the negotiation.
        description: Detailed description of the negotiation context.
        status: Current lifecycle status.
        initiated_by: The user who initiated the negotiation.
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
        related_name="negotiations",
        verbose_name=_("Proposal"),
        help_text=_("The proposal being negotiated."),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Human-readable title for the negotiation."),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("Detailed description of the negotiation context."),
    )
    status = models.CharField(
        max_length=20,
        choices=NegotiationStatus.choices,
        default=NegotiationStatus.OPEN,
        verbose_name=_("Status"),
        help_text=_("Current lifecycle status of the negotiation."),
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="initiated_negotiations",
        verbose_name=_("Initiated By"),
        help_text=_("The user who initiated the negotiation."),
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
        verbose_name = _("Negotiation")
        verbose_name_plural = _("Negotiations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["proposal", "status"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the negotiation."""
        return f"{self.title} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Check if the negotiation is currently active.

        Returns:
            True if the negotiation is OPEN or IN_PROGRESS.
        """
        return bool(self.status in (NegotiationStatus.OPEN, NegotiationStatus.IN_PROGRESS))

    @property
    def is_concluded(self) -> bool:
        """Check if the negotiation has concluded.

        Returns:
            True if the negotiation is AGREED, FAILED, or CANCELLED.
        """
        return bool(
            self.status
            in (
                NegotiationStatus.AGREED,
                NegotiationStatus.FAILED,
                NegotiationStatus.CANCELLED,
            )
        )
