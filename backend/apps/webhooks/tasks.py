"""Celery tasks for the webhooks app.

This module defines asynchronous tasks for delivering webhook payloads
to external systems with HMAC-SHA256 signature verification.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import requests
from celery import Task, shared_task

from apps.webhooks.models import WebhookSubscription

logger = logging.getLogger(__name__)

# Timeout for webhook HTTP requests (in seconds)
WEBHOOK_TIMEOUT = 10

# Number of retry attempts for failed webhook deliveries
WEBHOOK_MAX_RETRIES = 3


def _generate_signature(secret: str, payload: dict[str, Any]) -> str:
    """Generate an HMAC-SHA256 signature for the payload.

    Args:
        secret: The webhook subscription secret.
        payload: The JSON-serializable payload.

    Returns:
        The hex-encoded HMAC-SHA256 signature string.
    """
    import json

    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    secret_bytes = secret.encode("utf-8")

    signature = hmac.new(
        secret_bytes,
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={signature}"


@shared_task(
    bind=True,
    max_retries=WEBHOOK_MAX_RETRIES,
    default_retry_delay=60,  # Retry after 1 minute
)
def deliver_webhook_task(
    self: Task,
    subscription_id: str,
    payload: dict[str, Any],
    event_type: str,
) -> None:
    """Deliver a webhook payload to the configured URL.

    Args:
        subscription_id: The UUID of the webhook subscription.
        payload: The data payload to send.
        event_type: The type of event being sent.
    """
    try:
        subscription = WebhookSubscription.objects.get(id=subscription_id)
    except WebhookSubscription.DoesNotExist:
        logger.warning("Webhook subscription %s not found", subscription_id)
        return

    if not subscription.is_active or event_type not in subscription.active_events:
        logger.info(
            "Webhook subscription %s is no longer valid for %s", subscription_id, event_type
        )
        return

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Legatio-Webhook/1.0",
        "X-Legatio-Event": event_type,
        "X-Legatio-Signature": _generate_signature(subscription.secret, payload),
    }

    try:
        response = requests.post(
            subscription.url,
            json=payload,
            headers=headers,
            timeout=WEBHOOK_TIMEOUT,
        )
        response.raise_for_status()
        logger.info(
            "Webhook delivered successfully to %s for event %s (Status: %d)",
            subscription.url,
            event_type,
            response.status_code,
        )
    except requests.exceptions.RequestException as e:
        logger.warning(
            "Webhook delivery failed to %s for event %s: %s. Retrying...",
            subscription.url,
            event_type,
            str(e),
        )
        # Retry the task
        raise self.retry(exc=e)
