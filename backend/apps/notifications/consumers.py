"""Notification WebSocket consumer.

This module provides the WebSocket consumer for real-time notification
delivery. Implementation will be completed in Phase 7 Step 2.
"""

from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications.

    Placeholder implementation - will be completed in Step 2.
    """

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
