"""NegotiationOffer model definition.

This module defines the NegotiationOffer model, which represents an
individual offer or counter-offer made within a negotiation.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class OfferStatus(models.TextChoices):
    """Status lifecycle of a negotiation offer."""

    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REJECTED = "REJECTED", _("Rejected")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class NegotiationOffer(models.Model):
    """An offer or counter-offer within a negotiation.

    Offers carry the proposed terms and progress through a lifecycle
    as they are accepted, rejected, or withdrawn by the parties.

    Attributes:
        id: UUID primary key.
        negotiation: The negotiation this offer belongs to.
        offered_by: The user making the offer.
        terms: Structured JSON terms of the offer.
        status: Current offer status.
        round_number: Sequential round number within the negotiation.
        notes: Optional notes accompanying the offer.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    negotiation = models.ForeignKey(
        "negotiations.Negotiation",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("Negotiation"),
        help_text=_("The negotiation this offer belongs to."),
    )
    offered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="negotiation_offers",
        verbose_name=_("Offered By"),
        help_text=_("The user making the offer."),
    )
    terms = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Terms"),
        help_text=_("Structured JSON terms of the offer."),
    )
    status = models.CharField(
        max_length=20,
        choices=OfferStatus.choices,
        default=OfferStatus.PENDING,
        verbose_name=_("Status"),
        help_text=_("Current status of the offer."),
    )
    round_number = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Round Number"),
        help_text=_("Sequential round number within the negotiation."),
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Notes"),
        help_text=_("Optional notes accompanying the offer."),
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
        verbose_name = _("Negotiation Offer")
        verbose_name_plural = _("Negotiation Offers")
        ordering = ["negotiation", "-round_number", "-created_at"]
        indexes = [
            models.Index(fields=["negotiation", "status"]),
            models.Index(fields=["offered_by", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the offer."""
        return f"Offer round {self.round_number} ({self.status})"

    @property
    def is_pending(self) -> bool:
        """Check if the offer is still pending.

        Returns:
            True if the offer status is PENDING.
        """
        return bool(self.status == OfferStatus.PENDING)

    @property
    def is_resolved(self) -> bool:
        """Check if the offer has been resolved.

        Returns:
            True if the offer is ACCEPTED, REJECTED, or WITHDRAWN.
        """
        return bool(self.status != OfferStatus.PENDING)
