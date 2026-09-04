"""Tests for NotificationConsumer WebSocket behavior.

Tests cover connection authentication, group membership, and
notification delivery.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from channels.db import database_sync_to_async
from channels.layers import InMemoryChannelLayer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import User
from apps.notifications.consumers import NotificationConsumer
from apps.notifications.models import Notification, NotificationType
from apps.notifications.serializers import NotificationSerializer
from core.websocket_auth import JWTAuthMiddleware


@pytest.fixture(autouse=True)
async def _cleanup_pending_async_tasks() -> AsyncIterator[None]:
    """Cancel pending async tasks after each test.

    This prevents 'Task was destroyed but it is pending' warnings
    caused by the InMemoryChannelLayer's receive loop when the
    event loop closes.
    """
    yield

    import asyncio

    current = asyncio.current_task()
    pending = [task for task in asyncio.all_tasks() if task is not current and not task.done()]
    for task in pending:
        task.cancel()

    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


@database_sync_to_async
def create_user() -> User:
    """Create a test user asynchronously.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="ws@example.com", password="testpass123")


@database_sync_to_async
def create_notification(user: User) -> Notification:
    """Create a notification without triggering real-time delivery.

    Args:
        user: The recipient user.

    Returns:
        A Notification instance.
    """
    return Notification.objects.create(
        notification_type=NotificationType.SYSTEM,
        recipient=user,
        title="Test Notification",
        message="Test message",
    )


@pytest.fixture
def in_memory_channel_layer(monkeypatch: pytest.MonkeyPatch) -> InMemoryChannelLayer:
    """Provide an in-memory channel layer for WebSocket tests.

    This avoids requiring Redis during test execution.

    Args:
        monkeypatch: The pytest monkeypatch fixture.

    Returns:
        An InMemoryChannelLayer instance.
    """
    layer = InMemoryChannelLayer()

    def _get_layer(alias: str = "default") -> InMemoryChannelLayer:
        return layer

    monkeypatch.setattr("channels.layers.get_channel_layer", _get_layer)
    monkeypatch.setattr("channels.consumer.get_channel_layer", _get_layer, raising=False)

    return layer


def build_communicator(user: User | None = None) -> WebsocketCommunicator:
    """Build a WebSocket communicator with the consumer application.

    Args:
        user: Optional authenticated user for the scope.

    Returns:
        A WebsocketCommunicator instance.
    """
    application = JWTAuthMiddleware(NotificationConsumer.as_asgi())

    communicator = WebsocketCommunicator(application, "/ws/notifications/")

    if user is not None:
        communicator.scope["user"] = user
    else:
        communicator.scope["user"] = AnonymousUser()

    return communicator


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumer:
    """Tests for NotificationConsumer."""

    async def test_anonymous_connection_is_rejected(
        self, in_memory_channel_layer: InMemoryChannelLayer
    ) -> None:
        """Verify unauthenticated connections are closed."""
        communicator = build_communicator(user=None)

        connected, _ = await communicator.connect()

        assert connected is False

    async def test_authenticated_connection_is_accepted(
        self, in_memory_channel_layer: InMemoryChannelLayer
    ) -> None:
        """Verify authenticated connections are accepted."""
        user = await create_user()
        communicator = build_communicator(user=user)

        connected, _ = await communicator.connect()

        assert connected is True

        await communicator.disconnect()

    async def test_notification_sent_to_user_group(
        self, in_memory_channel_layer: InMemoryChannelLayer
    ) -> None:
        """Verify notifications are delivered to the connected user."""
        import json

        from rest_framework.renderers import JSONRenderer

        user = await create_user()
        communicator = build_communicator(user=user)

        connected, _ = await communicator.connect()
        assert connected is True

        notification = await create_notification(user)

        rendered = JSONRenderer().render(NotificationSerializer(notification).data)
        serialized = json.loads(rendered)

        await in_memory_channel_layer.group_send(
            f"notifications_{user.id}",
            {
                "type": "send_notification",
                "notification": serialized,
            },
        )

        response = await communicator.receive_json_from()
        assert response["type"] == "notification"
        assert response["data"]["title"] == "Test Notification"

        await communicator.disconnect()
