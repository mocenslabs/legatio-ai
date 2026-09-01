"""Notification serializer.

This module provides DRF serializers for the Notification model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model.

    Notifications are created by the service layer, so all fields are
    read-only. The is_read computed property is included for convenience.
    """

    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "recipient",
            "entity_type",
            "entity_id",
            "title",
            "message",
            "status",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
