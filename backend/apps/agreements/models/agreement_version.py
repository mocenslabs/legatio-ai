"""AgreementVersion model definition.

This module defines the AgreementVersion model, which records immutable
snapshots of an agreement's terms over time, enabling versioning and
amendment tracking.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AgreementVersion(models.Model):
    """An immutable snapshot of an agreement at a point in time.

    Every significant change to an agreement creates a new version,
    preserving the full history of terms and amendments.

    Attributes:
        id: UUID primary key.
        agreement: The agreement this version belongs to.
        version_number: Sequential version number (unique per agreement).
        title: Snapshot of the agreement title at this version.
        terms: Snapshot of the agreement terms at this version.
        change_reason: Description of why this version was created.
        created_by: User who created this version.
        created_at: Timestamp of creation.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    agreement = models.ForeignKey(
        "agreements.Agreement",
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Agreement"),
        help_text=_("The agreement this version belongs to."),
    )
    version_number = models.PositiveIntegerField(
        verbose_name=_("Version Number"),
        help_text=_("Sequential version number, unique per agreement."),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Snapshot of the agreement title at this version."),
    )
    terms = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Terms"),
        help_text=_("Snapshot of the agreement terms at this version."),
    )
    change_reason = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Change Reason"),
        help_text=_("Description of why this version was created."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agreement_versions",
        verbose_name=_("Created By"),
        help_text=_("User who created this version."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )

    class Meta:
        verbose_name = _("Agreement Version")
        verbose_name_plural = _("Agreement Versions")
        ordering = ["agreement", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "version_number"],
                name="unique_agreement_version_number",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement", "version_number"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the agreement version."""
        return f"{self.agreement_id} v{self.version_number}"
