"""AutomationRule model definition.

This module defines the AutomationRule model, which specifies when and how
an agent should act. Each rule defines a trigger, an optional condition,
and the action to execute.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TriggerType(models.TextChoices):
    """Types of events that can trigger an automation rule."""

    ON_PROPOSAL_CREATED = "ON_PROPOSAL_CREATED", _("On Proposal Created")
    ON_PROPOSAL_SUBMITTED = "ON_PROPOSAL_SUBMITTED", _("On Proposal Submitted")
    ON_PROPOSAL_STATUS_CHANGED = "ON_PROPOSAL_STATUS_CHANGED", _("On Proposal Status Changed")
    ON_SCHEDULE = "ON_SCHEDULE", _("On Schedule")
    MANUAL = "MANUAL", _("Manual")


class ActionType(models.TextChoices):
    """Types of actions an agent can execute."""

    CREATE_PROPOSAL = "CREATE_PROPOSAL", _("Create Proposal")
    APPROVE_PROPOSAL = "APPROVE_PROPOSAL", _("Approve Proposal")
    REJECT_PROPOSAL = "REJECT_PROPOSAL", _("Reject Proposal")
    ADD_COMMENT = "ADD_COMMENT", _("Add Comment")
    NOTIFY = "NOTIFY", _("Notify")
    CUSTOM = "CUSTOM", _("Custom")


class AutomationRule(models.Model):
    """A rule defining when and how an agent acts.

    Automation rules connect a trigger event, an optional condition, and
    an action to execute. When the trigger fires and the condition is met,
    the agent executes the configured action.

    Attributes:
        id: UUID primary key.
        agent: The agent that owns this rule.
        name: Human-readable name for the rule.
        trigger_type: The event that triggers the rule.
        condition: JSON condition that must be met for the rule to fire.
        action_type: The action the agent executes.
        action_config: JSON configuration for the action.
        priority: Priority for ordering rule evaluation.
        is_active: Whether the rule is currently active.
        created_by: The user who created the rule.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        related_name="rules",
        verbose_name=_("Agent"),
        help_text=_("The agent that owns this rule."),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Human-readable name for the rule."),
    )
    trigger_type = models.CharField(
        max_length=50,
        choices=TriggerType.choices,
        verbose_name=_("Trigger Type"),
        help_text=_("The event that triggers the rule."),
    )
    condition = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Condition"),
        help_text=_("JSON condition that must be met for the rule to fire."),
    )
    action_type = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        verbose_name=_("Action Type"),
        help_text=_("The action the agent executes."),
    )
    action_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Action Config"),
        help_text=_("JSON configuration for the action."),
    )
    priority = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Priority"),
        help_text=_("Priority for ordering rule evaluation. Lower runs first."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether the rule is currently active."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="automation_rules",
        verbose_name=_("Created By"),
        help_text=_("The user who created the rule."),
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
        verbose_name = _("Automation Rule")
        verbose_name_plural = _("Automation Rules")
        ordering = ["priority", "-created_at"]
        indexes = [
            models.Index(fields=["agent", "is_active"]),
            models.Index(fields=["trigger_type", "is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the automation rule."""
        return f"{self.name} ({self.trigger_type} -> {self.action_type})"

    @property
    def can_fire(self) -> bool:
        """Check if the rule can fire.

        Returns:
            True if the rule is active and the agent is active.
        """
        return bool(self.is_active and self.agent.is_active)

    @property
    def has_condition(self) -> bool:
        """Check if the rule has a condition configured.

        Returns:
            True if the condition is not empty.
        """
        return bool(self.condition)
