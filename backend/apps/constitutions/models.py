"""
Models for the constitutions app.
Defines Constitution, ConstitutionVersion, and PolicyRule models.
These are the heart of Legatio: users define rules that the Policy Engine evaluates.
Source: 03-DATA-MODEL.md Section 8
"""

import uuid
from typing import Any

from django.conf import settings
from django.db import models

from apps.constitutions.managers import (
    ConstitutionSoftDeleteManager,
    ImmutableVersionManager,
)
from core.enums import (
    ConstitutionStatus,
    RuleAction,
    RuleCategory,
    RuleOperator,
)


class Constitution(models.Model):
    """
    Mutable container for a set of rules.
    A Constitution belongs to an Agent and can have multiple versions.
    Only one Constitution per Agent can be ACTIVE at a time (enforced by partial unique index).
    Source: 03-DATA-MODEL.md Section 8.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    agent = models.ForeignKey(
        "agents.Agent",
        on_delete=models.CASCADE,
        related_name="constitutions",
        help_text="Agent that owns this constitution.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name, e.g., 'Travel Constitution'.",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Optional description of the constitution's purpose.",
    )
    status = models.CharField(
        max_length=20,
        choices=ConstitutionStatus.choices,
        default=ConstitutionStatus.DRAFT,
        db_index=True,
    )
    active_version = models.ForeignKey(
        "constitutions.ConstitutionVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Currently enforced version. Null if no version is active.",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        help_text="Soft delete timestamp.",
    )

    # Manager
    objects = ConstitutionSoftDeleteManager()
    all_objects = models.Manager()  # noqa: DJ012

    class Meta:
        db_table = "legatio_constitutions_constitution"
        verbose_name = "constitution"
        verbose_name_plural = "constitutions"
        ordering = ["-created_at"]
        constraints: list[Any] = []

    def __str__(self) -> str:
        return f"{self.name} ({self.get_status_display()})"

    @property
    def owner(self) -> Any:
        """Return the owner via agent chain (for IsOwner permission)."""
        return self.agent.owner

    def soft_delete(self) -> None:
        """Soft-delete this constitution."""
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    @property
    def is_deleted(self) -> bool:
        """Check if the constitution is soft-deleted."""
        return self.deleted_at is not None


class ConstitutionVersion(models.Model):
    """
    Immutable snapshot of rules.
    Once activated, a ConstitutionVersion cannot be modified.
    Edits create a new version with version_number + 1.
    Source: 03-DATA-MODEL.md Section 8.2
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    constitution = models.ForeignKey(
        Constitution,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="Constitution that this version belongs to.",
    )
    version_number = models.PositiveIntegerField(
        help_text="Sequential version number per constitution.",
    )
    status = models.CharField(
        max_length=20,
        choices=ConstitutionStatus.choices,
        default=ConstitutionStatus.DRAFT,
        db_index=True,
    )
    rules_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full serialized rules for fast load.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_versions",
        help_text="User who created this version.",
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this version was activated.",
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this version was archived.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Manager
    objects = ImmutableVersionManager()

    class Meta:
        db_table = "legatio_constitutions_constitutionversion"
        verbose_name = "constitution version"
        verbose_name_plural = "constitution versions"
        ordering = ["constitution", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["constitution", "version_number"],
                name="uniq_version_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.constitution.name} v{self.version_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to enforce immutability.
        Once a version is ACTIVE or ARCHIVED, its content cannot be modified.
        Lifecycle state transitions (ACTIVE -> ARCHIVED) are allowed when
        only status and timestamp fields are updated.
        """
        if self.pk:
            try:
                existing = ConstitutionVersion.objects.get(pk=self.pk)
                if existing.status in [
                    ConstitutionStatus.ACTIVE,
                    ConstitutionStatus.ARCHIVED,
                ]:
                    # Allow lifecycle transitions: only status + timestamps
                    update_fields = kwargs.get("update_fields")
                    allowed_lifecycle_fields = {"status", "archived_at", "activated_at"}
                    is_lifecycle_transition = update_fields is not None and set(
                        update_fields
                    ).issubset(allowed_lifecycle_fields)
                    if not is_lifecycle_transition:
                        raise RuntimeError(
                            f"ConstitutionVersion {self.pk} is immutable "
                            f"(status={existing.status})."
                        )
            except ConstitutionVersion.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @property
    def owner(self) -> Any:
        """Return the owner via constitution → agent chain."""
        return self.constitution.agent.owner


class PolicyRule(models.Model):
    """
    Individual rule within a ConstitutionVersion.
    Rules are immutable and belong to a specific version.
    The Policy Engine evaluates these rules against proposed actions.
    Source: 03-DATA-MODEL.md Section 8.3
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    version = models.ForeignKey(
        ConstitutionVersion,
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="ConstitutionVersion that this rule belongs to.",
    )
    rule_number = models.PositiveIntegerField(
        help_text="Display number, e.g., 'Rule #17'.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name, e.g., 'Never share phone'.",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Human-readable explanation of the rule.",
    )
    category = models.CharField(
        max_length=20,
        choices=RuleCategory.choices,
        db_index=True,
    )
    field = models.CharField(
        max_length=100,
        help_text="Field to evaluate, e.g., 'phone_number', 'amount'.",
    )
    operator = models.CharField(
        max_length=30,
        choices=RuleOperator.choices,
    )
    value = models.JSONField(
        help_text="Typed value (number, string, list).",
    )
    action = models.CharField(
        max_length=20,
        choices=RuleAction.choices,
        default=RuleAction.DENY,
        help_text="Action to take when rule matches. Default: DENY (fail-safe).",
    )
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Evaluation priority. Lower = evaluated first.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rule is active.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "legatio_constitutions_policyrule"
        verbose_name = "policy rule"
        verbose_name_plural = "policy rules"
        ordering = ["version", "priority", "rule_number"]
        indexes = [
            models.Index(
                fields=["version", "priority"],
                name="idx_policyrule_versionpriority",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["version", "rule_number"],
                name="uniq_rule_number",
            ),
        ]

    def __str__(self) -> str:
        return f"Rule #{self.rule_number}: {self.name}"

    @property
    def owner(self) -> Any:
        """Return the owner via version → constitution → agent chain."""
        return self.version.constitution.agent.owner
