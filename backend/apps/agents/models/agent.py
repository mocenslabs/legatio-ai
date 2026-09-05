"""Agent model definition.

This module defines the Agent model, which represents an automated actor
capable of performing actions within the governance system, such as
creating proposals, approving based on criteria, or monitoring events.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AgentType(models.TextChoices):
    """Types of agents."""

    AUTO_PROPOSER = "AUTO_PROPOSER", _("Auto Proposer")
    AUTO_APPROVER = "AUTO_APPROVER", _("Auto Approver")
    MONITOR = "MONITOR", _("Monitor")
    CUSTOM = "CUSTOM", _("Custom")


class Agent(models.Model):
    """An automated actor within the governance system.

    Agents can be configured to perform actions automatically based
    on automation rules. Each agent has a type that determines its
    primary behavior and a JSON config for type-specific settings.

    Attributes:
        id: UUID primary key.
        name: Human-readable name for the agent.
        description: Detailed description of the agent's purpose.
        agent_type: The category of agent behavior.
        config: JSON configuration specific to the agent type.
        is_active: Whether the agent is currently active.
        created_by: The user who created the agent.
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
        verbose_name=_("Name"),
        help_text=_("Human-readable name for the agent."),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("Detailed description of the agent's purpose."),
    )
    agent_type = models.CharField(
        max_length=50,
        choices=AgentType.choices,
        verbose_name=_("Agent Type"),
        help_text=_("The category of agent behavior."),
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Config"),
        help_text=_("JSON configuration specific to the agent type."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether the agent is currently active."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agents",
        verbose_name=_("Created By"),
        help_text=_("The user who created the agent."),
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
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agent_type", "is_active"]),
            models.Index(fields=["created_by", "is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the agent."""
        return f"{self.name} ({self.agent_type})"

    @property
    def can_execute(self) -> bool:
        """Check if the agent can execute actions.

        Returns:
            True if the agent is active.
        """
        return bool(self.is_active)
