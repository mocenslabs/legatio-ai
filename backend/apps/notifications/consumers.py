"""Notification WebSocket consumer.

This module provides the WebSocket consumer for real-time notification
delivery. Authenticated users connect to receive their notifications
instantly as they are created by the NotificationService.
"""

from __future__ import annotations

import logging
from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications.

    Each authenticated user is added to a personal group named
    'notifications_{user_id}'. When the NotificationService creates
    a notification, it sends a message to this group, which triggers
    the send_notification handler to push the notification to the user.

    Attributes:
        group_name: The channel layer group name for this user.
    """

    group_name: str = ""

    async def connect(self) -> None:
        """Handle WebSocket connection.

        Verifies that the user is authenticated, joins them to their
        personal notification group, and accepts the connection.
        Unauthenticated connections are closed immediately.
        """
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt rejected")
            await self.close()
            return

        # Create a unique group name for this user
        self.group_name = f"notifications_{user.id}"

        # Join the user's notification group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        logger.info(
            "WebSocket connected for user %s, joined group %s",
            user.id,
            self.group_name,
        )
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection.

        Leaves the user's notification group.

        Args:
            close_code: The WebSocket close code.
        """
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(
                "WebSocket disconnected (code %s), left group %s",
                close_code,
                self.group_name,
            )

    async def send_notification(self, event: dict[str, Any]) -> None:
        """Handle a notification event from the channel layer.

        This method is called when the NotificationService sends a
        notification to the user's group via the channel layer.

        Args:
            event: The notification event data containing:
                - type: The event type (always 'send_notification')
                - notification: The serialized notification data
        """
        notification_data = event.get("notification", {})
        await self.send_json(
            {
                "type": "notification",
                "data": notification_data,
            }
        )
        logger.debug(
            "Sent notification to group %s: %s",
            self.group_name,
            notification_data.get("title", "untitled"),
        )

    async def receive_json(self, content: dict[str, Any], **kwargs: Any) -> None:
        """Handle incoming JSON messages from the client.

        Currently no client-to-server messages are supported.
        This can be extended in the future for marking notifications
        as read or other actions.

        Args:
            content: The parsed JSON content from the client.
            **kwargs: Additional keyword arguments.
        """
        logger.debug("Received message from client: %s", content)
        # For now, we don't support client-to-server messages
        # This can be extended to handle mark_as_read, etc.
