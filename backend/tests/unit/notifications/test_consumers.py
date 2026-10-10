"""Unit tests for WebSocket consumers."""

from typing import Any
from uuid import uuid4

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from apps.accounts.services.auth import generate_access_token
from apps.notifications.consumers import NotificationConsumer
from apps.notifications.middleware import JWTAuthMiddleware

User = get_user_model()


@pytest.fixture
def channel_layer_settings(settings: Any) -> Any:
    """Use InMemoryChannelLayer for tests."""
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    return settings


@pytest.fixture
def application(channel_layer_settings: Any) -> Any:
    """Build ASGI application with JWT middleware."""
    return JWTAuthMiddleware(NotificationConsumer.as_asgi())


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumer:
    async def test_connect_authenticated(self, application: Any) -> None:
        """Authenticated user can connect."""
        user = await sync_to_async(User.objects.create_user)(
            email="ws1@example.com", password="pass"
        )
        token = await sync_to_async(generate_access_token)(user)

        communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        connected, _ = await communicator.connect()
        assert connected, "Should connect successfully"

        response = await communicator.receive_json_from()
        assert response["type"] == "connection.established"
        assert response["payload"]["user_id"] == str(user.id)
        assert "negotiation_rooms" in response["payload"]

        await communicator.disconnect()

    async def test_connect_unauthenticated_rejected(self, application: Any) -> None:
        """Unauthenticated connection is rejected."""
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        connected, _ = await communicator.connect()
        assert not connected, "Should reject unauthenticated connection"
        await communicator.disconnect()

    async def test_connect_invalid_token_rejected(self, application: Any) -> None:
        """Invalid token is rejected."""
        communicator = WebsocketCommunicator(application, "/ws/notifications/?token=invalid-token")
        connected, _ = await communicator.connect()
        assert not connected, "Should reject invalid token"
        await communicator.disconnect()

    async def test_subscribe_to_negotiation(self, application: Any) -> None:
        """User can subscribe to additional negotiation rooms."""
        user = await sync_to_async(User.objects.create_user)(
            email="ws2@example.com", password="pass"
        )
        token = await sync_to_async(generate_access_token)(user)

        communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()

        await communicator.send_json_to(
            {
                "type": "subscribe",
                "payload": {"negotiation_ids": [str(uuid4())]},
            }
        )

        response = await communicator.receive_json_from()
        assert response["type"] == "subscription.confirmed"

        await communicator.disconnect()
