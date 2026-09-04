"""Notifications services.

This module exports the service classes for notification operations.
"""

from apps.notifications.services.notification_service import NotificationService
from apps.notifications.services.realtime import send_realtime_notification

__all__ = ["NotificationService", "send_realtime_notification"]
