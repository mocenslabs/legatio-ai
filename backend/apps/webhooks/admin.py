"""Webhooks admin configuration.

This module registers the WebhookSubscription model with the Django admin
interface for administrative management.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.webhooks.models import WebhookSubscription


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for WebhookSubscription model.

    Provides full CRUD operations for administrative management of
    webhook subscriptions. The secret field is displayed but marked
    as sensitive information.
    """

    list_display = [
        "name",
        "url",
        "is_active",
        "event_count",
        "created_by",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "url"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "secret", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "name", "url", "is_active")}),
        (
            "Security",
            {
                "fields": ("secret",),
                "description": "The secret is used to sign webhook payloads with HMAC-SHA256. "
                "Keep this value confidential.",
            },
        ),
        ("Events", {"fields": ("events",)}),
        ("Ownership", {"fields": ("created_by",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Events")
    def event_count(self, obj: WebhookSubscription) -> int:
        """Return the number of subscribed events.

        Args:
            obj: The webhook subscription instance.

        Returns:
            The count of subscribed events.
        """
        return len(obj.active_events)

    def get_queryset(self, request: HttpRequest) -> QuerySet[WebhookSubscription]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of WebhookSubscription objects.
        """
        return super().get_queryset(request).select_related("created_by")
