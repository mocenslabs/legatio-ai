"""Real-time notification delivery via WebSocket.

This module provides functions to push notifications to connected users
through the Channels layer. It is designed to be non-blocking and
fail-safe: if the channel layer is unavailable or fails, notifications
are still created in the database.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def send_realtime_notification(
    recipient_id: uuid.UUID,
    notification_data: dict[str, Any],
) -> None:
    """Send a notification to a user via WebSocket.

    This function sends a message to the user's personal notification
    group via the channel layer. It is designed to be fail-safe: if the
    channel layer is unavailable or an error occurs, the notification
    is still persisted in the database.

    Args:
        recipient_id: The UUID of the user to notify.
        notification_data: The serialized notification data to send.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Channel layer not available. Real-time notifications disabled.")
        return

    group_name = f"notifications_{recipient_id}"

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "notification": notification_data,
            },
        )
        logger.debug(
            "Sent real-time notification to group %s: %s",
            group_name,
            notification_data.get("title", "untitled"),
        )
    except Exception as e:
        # Fail-safe: log the error but don't break the notification creation
        logger.exception(
            "Failed to send real-time notification to %s: %s",
            group_name,
            str(e),
        )
