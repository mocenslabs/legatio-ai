"""
WebSocket URL routing for Django Channels.
Source: 02-ARCHITECTURE.md Section 10.1
"""

from django.urls import path

from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]
