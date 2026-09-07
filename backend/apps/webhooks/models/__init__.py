"""Webhooks models.

This module exports all models from the webhooks app.
"""

from apps.webhooks.models.webhook_subscription import WebhookEventType, WebhookSubscription

__all__ = ["WebhookEventType", "WebhookSubscription"]
