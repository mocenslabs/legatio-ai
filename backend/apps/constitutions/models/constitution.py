"""Constitution model definition.

This module defines the Constitution model, which represents the foundational
ruleset or governance framework under which policy rules operate.

A Constitution belongs to a specific User (owner) and contains multiple
PolicyRules that define the governance behavior for that user's operations.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Constitution(models.Model):
    """A governance framework or ruleset for the system.

    Each Constitution is owned by a specific user and defines the rules
    under which that user's agents and proposals operate. The name must
    be unique per user, but can be repeated across different users.

    Attributes:
        id: UUID primary key.
        user: The user who owns this constitution.
        name: Human-readable name of the constitution (unique per user).
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="constitutions",
        verbose_name=_("User"),
        help_text=_("The user who owns this constitution."),
    )
    name = models.CharField(
        max_length=255,
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
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_constitution_user_created"),
            models.Index(fields=["user", "is_active"], name="idx_constitution_user_active"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_constitution_name_per_user",
            ),
        ]

    def __str__(self) -> str:
        """Return string representation of the constitution."""
        # mypy-safe way to access user.email when user might be typed as Optional
        user_email = self.user.email if self.user else "Unknown"
        return f"{self.name} ({user_email})"
