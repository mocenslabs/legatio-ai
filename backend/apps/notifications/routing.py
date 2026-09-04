"""WebSocket URL routing for the notifications app.

This module defines the WebSocket URL patterns for real-time
notification delivery.
"""

from __future__ import annotations

from django.urls import path

from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]
