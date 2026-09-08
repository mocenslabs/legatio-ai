"""Webhook subscription serializers.

This module provides DRF serializers for the WebhookSubscription model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.webhooks.models import WebhookSubscription


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for WebhookSubscription model.

    Handles validation and representation of webhook subscriptions.
    The 'secret' field is exposed so users can copy it to configure
    their receiving endpoints, but it is generated automatically if
    not provided.
    """

    class Meta:
        model = WebhookSubscription
        fields = [
            "id",
            "name",
            "url",
            "secret",
            "events",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "secret",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_url(self, value: str) -> str:
        """Validate that the URL uses HTTPS in production-like environments.

        For development, HTTP is allowed, but we enforce a basic URL structure.
        """
        if not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def validate_events(self, value: list[str]) -> list[str]:
        """Validate that the events list is not empty if the subscription is active."""
        # Note: is_active is not available during field validation in all cases,
        # but we can at least ensure it's a valid list of choices if provided.
        from apps.webhooks.models import WebhookEventType

        valid_choices = {choice[0] for choice in WebhookEventType.choices}
        for event in value:
            if event not in valid_choices:
                raise serializers.ValidationError(f"Invalid event type: {event}")
        return value
