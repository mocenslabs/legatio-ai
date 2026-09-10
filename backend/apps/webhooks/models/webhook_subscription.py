"""WebhookSubscription model definition.

This module defines the WebhookSubscription model, which allows external
systems to subscribe to specific events in the Legatio system and receive
HTTP POST notifications.
"""

from __future__ import annotations

import secrets
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _


def generate_webhook_secret() -> str:
    return secrets.token_hex(32)


class WebhookEventType(models.TextChoices):
    """Types of events that can trigger a webhook."""

    PROPOSAL_CREATED = "PROPOSAL_CREATED", _("Proposal Created")
    PROPOSAL_STATUS_CHANGED = "PROPOSAL_STATUS_CHANGED", _("Proposal Status Changed")
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED", _("Approval Requested")
    APPROVAL_RESOLVED = "APPROVAL_RESOLVED", _("Approval Resolved")
    AGREEMENT_ACTIVATED = "AGREEMENT_ACTIVATED", _("Agreement Activated")
    AGREEMENT_TERMINATED = "AGREEMENT_TERMINATED", _("Agreement Terminated")
    NEGOTIATION_STARTED = "NEGOTIATION_STARTED", _("Negotiation Started")
    NEGOTIATION_AGREED = "NEGOTIATION_AGREED", _("Negotiation Agreed")
    NEGOTIATION_FAILED = "NEGOTIATION_FAILED", _("Negotiation Failed")


class WebhookSubscription(models.Model):
    """A subscription for external systems to receive event notifications.

    When a subscribed event occurs, the system sends an HTTP POST request
    to the configured URL with a JSON payload and an HMAC signature for
    security verification.

    Attributes:
        id: UUID primary key.
        name: Human-readable name for the subscription.
        url: The target URL to receive webhook payloads.
        secret: Secret key used to generate HMAC signatures.
        events: List of event types this subscription listens to.
        is_active: Whether the subscription is currently active.
        created_by: The user who created the subscription.
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
        help_text=_("Human-readable name for the subscription."),
    )
    url = models.URLField(
        max_length=500,
        verbose_name=_("URL"),
        help_text=_("The target URL to receive webhook payloads."),
    )
    secret = models.CharField(
        max_length=128,
        default=generate_webhook_secret,
        verbose_name=_("Secret"),
        help_text=_("Secret key used to generate HMAC signatures."),
    )
    events = ArrayField(
        models.CharField(max_length=50, choices=WebhookEventType.choices),
        default=list,
        blank=True,
        verbose_name=_("Events"),
        help_text=_("List of event types this subscription listens to."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether the subscription is currently active."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webhook_subscriptions",
        verbose_name=_("Created By"),
        help_text=_("The user who created the subscription."),
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
        verbose_name = _("Webhook Subscription")
        verbose_name_plural = _("Webhook Subscriptions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the webhook subscription."""
        return f"{self.name} ({self.url})"

    @property
    def active_events(self) -> list[str]:
        """Return list of active event types for this subscription.

        Returns:
            List of event type strings.
        """
        return [event for event in self.events if event]
