"""
Models for the agents app.
Defines the Agent model, which represents an AI agent that acts on behalf
of a user or as an external agent.
Source: 03-DATA-MODEL.md Section 7.1
"""

import uuid
from typing import Any

from django.conf import settings
from django.db import models

from apps.agents.managers import SoftDeleteManager
from core.enums import AgentStatus, AgentType


class Agent(models.Model):
    """
    An AI agent that acts on behalf of a user or as an external agent.
    Agents are user-facing entities and use soft deletes.
    Each agent belongs to a user (owner) or is an external agent (owner=null).
    Source: 03-DATA-MODEL.md Section 7.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="agents",
        help_text="User who owns this agent. Null for external agents.",
    )
    agent_type = models.CharField(
        max_length=20,
        choices=AgentType.choices,
        db_index=True,
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name for the agent.",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Optional description of the agent's purpose.",
    )
    status = models.CharField(
        max_length=20,
        choices=AgentStatus.choices,
        default=AgentStatus.ACTIVE,
        db_index=True,
    )
    external_endpoint_url = models.URLField(
        default="",
        blank=True,
        help_text="Endpoint URL for external agents.",
    )
    capabilities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of advertised capabilities.",
    )
    protocol_version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Protocol version supported by the agent.",
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
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # noqa: DJ012

    class Meta:
        db_table = "legatio_agents_agent"
        verbose_name = "agent"
        verbose_name_plural = "agents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"], name="idx_agent_owner"),
            models.Index(fields=["agent_type"], name="idx_agent_type"),
            models.Index(fields=["status"], name="idx_agent_status"),
        ]
        constraints: list[Any] = []

    def __str__(self) -> str:
        return f"{self.name} ({self.get_agent_type_display()})"

    def soft_delete(self) -> None:
        """Soft-delete this agent."""
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def restore(self) -> None:
        """Restore a soft-deleted agent."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])

    @property
    def is_deleted(self) -> bool:
        """Check if the agent is soft-deleted."""
        return self.deleted_at is not None


class Credential(models.Model):
    """
    API credentials for agent authentication.

    The full API key is shown only once at creation and never stored.
    Only the SHA-256 hash is persisted for verification.

    Source: 03-DATA-MODEL.md Section 7.2
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="credentials",
        help_text="Agent that owns this credential.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name, e.g., 'production-key'.",
    )
    key_prefix = models.CharField(
        max_length=16,
        unique=True,
        help_text="Visible prefix of the key, e.g., 'lgat_4f2a'.",
    )
    key_hash = models.CharField(
        max_length=128,
        unique=True,
        help_text="SHA-256 hash of the full API key.",
    )
    scopes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of permitted scopes, e.g., ['negotiate', 'propose'].",
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this credential was used.",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expiration timestamp. Null = never expires.",
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Revocation timestamp. Null = active.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "legatio_agents_credential"
        verbose_name = "credential"
        verbose_name_plural = "credentials"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agent"], name="idx_credential_agent"),
            models.Index(fields=["key_prefix"], name="idx_credential_prefix"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.key_prefix}...)"

    @property
    def is_active(self) -> bool:
        """Check if the credential is active (not revoked and not expired)."""
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None:
            from django.utils import timezone

            return self.expires_at > timezone.now()
        return True

    def revoke(self) -> None:
        """Revoke this credential."""
        from django.utils import timezone

        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])
