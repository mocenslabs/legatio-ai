"""Agreement model definition.

This module defines the Agreement model, which represents a formal agreement
generated from an approved proposal. Agreements have a lifecycle, versioning,
and can include structured terms.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AgreementStatus(models.TextChoices):
    """Status lifecycle of an agreement."""

    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    SUSPENDED = "SUSPENDED", _("Suspended")
    COMPLETED = "COMPLETED", _("Completed")
    TERMINATED = "TERMINATED", _("Terminated")


class Agreement(models.Model):
    """A formal agreement generated from an approved proposal.

    Agreements represent binding commitments between parties. They are
    typically generated when a proposal is executed, but can also be
    created directly.

    Attributes:
        id: UUID primary key.
        title: Human-readable title for the agreement.
        description: Detailed description of the agreement.
        proposal: Optional link to the originating proposal.
        constitution: Optional link to a specific constitution.
        status: Current lifecycle status.
        terms: Structured JSON terms of the agreement.
        effective_date: Date when the agreement becomes active.
        expiration_date: Optional date when the agreement expires.
        created_by: User who created the agreement.
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
        help_text=_("Human-readable title for the agreement."),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("Detailed description of the agreement."),
    )
    proposal = models.ForeignKey(
        "proposals.Proposal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agreements",
        verbose_name=_("Proposal"),
        help_text=_("Optional link to the originating proposal."),
    )
    constitution = models.ForeignKey(
        "constitutions.Constitution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agreements",
        verbose_name=_("Constitution"),
        help_text=_("Optional link to a specific constitution."),
    )
    status = models.CharField(
        max_length=20,
        choices=AgreementStatus.choices,
        default=AgreementStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Current lifecycle status of the agreement."),
    )
    terms = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Terms"),
        help_text=_("Structured JSON terms of the agreement."),
    )
    effective_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Effective Date"),
        help_text=_("Date when the agreement becomes active."),
    )
    expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expiration Date"),
        help_text=_("Optional date when the agreement expires."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agreements",
        verbose_name=_("Created By"),
        help_text=_("User who created the agreement."),
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
        verbose_name = _("Agreement")
        verbose_name_plural = _("Agreements")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["effective_date", "expiration_date"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the agreement."""
        return f"{self.title} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Check if the agreement is currently active.

        Returns:
            True if the agreement status is ACTIVE.
        """
        return bool(self.status == AgreementStatus.ACTIVE)

    @property
    def is_expired(self) -> bool:
        """Check if the agreement has expired.

        Returns:
            True if the expiration_date has passed.
        """
        from django.utils import timezone

        if self.expiration_date is None:
            return False
        return bool(self.expiration_date < timezone.now())

    @property
    def can_be_activated(self) -> bool:
        """Check if the agreement can be activated.

        Returns:
            True if the agreement is in DRAFT status.
        """
        return bool(self.status == AgreementStatus.DRAFT)
