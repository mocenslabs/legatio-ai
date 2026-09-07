"""Webhook Service layer.

This module provides a service for triggering and managing webhook
deliveries to external systems.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.webhooks.models import WebhookSubscription
from apps.webhooks.tasks import deliver_webhook_task

logger = logging.getLogger(__name__)


class WebhookService:
    """Service layer for webhook operations.

    Handles finding matching subscriptions for an event and dispatching
    them to a Celery task for asynchronous delivery."""

    @staticmethod
    def trigger_event(event_type: str, payload: dict[str, Any]) -> int:
        """Trigger webhooks for a specific event type.

        Finds all active subscriptions that listen to the given event
        type and dispatches them to a Celery task for delivery.

        Args:
            event_type: The type of event that occurred.
            payload: The data payload to send.

        Returns:
            The number of webhooks dispatched.
        """
        subscriptions = WebhookSubscription.objects.filter(
            is_active=True,
            events__contains=[event_type],
        )

        dispatched_count = 0
        for subscription in subscriptions:
            try:
                deliver_webhook_task.delay(
                    subscription_id=str(subscription.id),
                    payload=payload,
                    event_type=event_type,
                )
                dispatched_count += 1
            except Exception as e:
                logger.exception(
                    "Failed to dispatch webhook task for subscription %s: %s",
                    subscription.id,
                    str(e),
                )

        logger.info(
            "Dispatched %d webhooks for event %s",
            dispatched_count,
            event_type,
        )
        return dispatched_count
