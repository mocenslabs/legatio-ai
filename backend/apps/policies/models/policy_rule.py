"""PolicyRule model definition.

This module defines the PolicyRule model, which represents deterministic
rules that govern what actions are allowed, denied, or require human approval
within the Legatio system.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class RuleActionType(models.TextChoices):
    """Types of actions a rule can enforce."""

    ALLOW = "ALLOW", _("Allow")
    DENY = "DENY", _("Deny")
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL", _("Require Approval")


class PolicyRule(models.Model):
    """A deterministic rule that governs actions within the system.

    Each rule has a condition (stored as JSON), an action type, and metadata
    that determines how the policy engine evaluates proposed actions.

    Attributes:
        id: UUID primary key.
        name: Human-readable name of the rule.
        description: Detailed description of what the rule enforces.
        condition: JSON structure defining when the rule applies.
        action_type: What action to take when the condition is met.
        risk_level: The risk level associated with this rule.
        requires_approval_from: JSON list of roles/users required for approval.
        priority: Execution priority (lower = evaluated first).
        is_active: Whether the rule is currently active.
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
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Name"),
        help_text=_("Human-readable name of the rule."),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("Detailed description of what the rule enforces."),
    )
    condition = models.JSONField(
        verbose_name=_("Condition"),
        help_text=_(
            "JSON structure defining when the rule applies. "
            "Example: {'field': 'amount', 'operator': '>', 'value': 10000}"
        ),
    )
    action_type = models.CharField(
        max_length=20,
        choices=RuleActionType.choices,
        verbose_name=_("Action Type"),
        help_text=_("What action to take when the condition is met."),
    )
    risk_level = models.CharField(
        max_length=10,
        choices=[
            ("LOW", _("Low")),
            ("MEDIUM", _("Medium")),
            ("HIGH", _("High")),
            ("CRITICAL", _("Critical")),
        ],
        default="LOW",
        verbose_name=_("Risk Level"),
        help_text=_("The risk level associated with this rule."),
    )
    requires_approval_from = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Requires Approval From"),
        help_text=_(
            "JSON list of roles or user UUIDs required for approval. "
            "Only used when action_type is REQUIRE_APPROVAL."
        ),
    )
    priority = models.IntegerField(
        default=100,
        verbose_name=_("Priority"),
        help_text=_("Execution priority (lower = evaluated first)."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether the rule is currently active."),
    )
    constitution = models.ForeignKey(
        "constitutions.Constitution",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="policy_rules",
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
        verbose_name = _("Policy Rule")
        verbose_name_plural = _("Policy Rules")
        ordering = ["priority", "created_at"]
        indexes = [
            models.Index(fields=["is_active", "priority"]),
            models.Index(fields=["constitution", "is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the rule."""
        return f"{self.name} ({self.action_type})"
