"""Unit tests for real-time notification delivery helper.

Tests cover fail-safe behavior when the channel layer is unavailable.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from apps.notifications.services.realtime import send_realtime_notification


class TestSendRealtimeNotification:
    """Tests for send_realtime_notification helper."""

    def test_does_not_raise_when_channel_layer_is_none(self) -> None:
        """Verify fail-safe behavior when channel layer is unavailable."""
        with patch(
            "apps.notifications.services.realtime.get_channel_layer",
            return_value=None,
        ):
            send_realtime_notification(
                recipient_id=uuid.uuid4(),
                notification_data={"title": "Test"},
            )

    def test_does_not_raise_when_group_send_fails(self) -> None:
        """Verify fail-safe behavior when group_send raises an error."""

        class FailingChannelLayer:
            """A channel layer stub that fails on group_send."""

            async def group_send(self, group: str, message: dict) -> None:
                """Raise an error to simulate failure.

                Args:
                    group: The group name.
                    message: The message payload.

                Raises:
                    RuntimeError: Always.
                """
                raise RuntimeError("Channel layer failure")

        with patch(
            "apps.notifications.services.realtime.get_channel_layer",
            return_value=FailingChannelLayer(),
        ):
            send_realtime_notification(
                recipient_id=uuid.uuid4(),
                notification_data={"title": "Test"},
            )
