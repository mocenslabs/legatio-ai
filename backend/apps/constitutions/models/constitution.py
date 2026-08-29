"""Constitution model definition.

This module defines the Constitution model, which represents the foundational
ruleset or governance framework under which policy rules operate.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Constitution(models.Model):
    """A governance framework or ruleset for the system.

    Attributes:
        id: UUID primary key.
        name: Human-readable name of the constitution.
        description: Detailed description of the governance framework.
        is_active: Whether this constitution is currently active.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Name"),
        help_text=_("Human-readable name of the constitution."),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("Detailed description of the governance framework."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this constitution is currently active."),
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
        verbose_name = _("Constitution")
        verbose_name_plural = _("Constitutions")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation of the constitution."""
        return self.name
