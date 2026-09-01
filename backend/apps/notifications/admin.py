"""Notifications admin configuration.

This module registers the Notification model with the Django admin interface.
Notifications are managed by the service layer, so the admin is read-only.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model (read-only).

    Notifications are created by the service layer. This admin provides
    visibility but prevents manual creation or modification.
    """

    list_display = [
        "title",
        "notification_type",
        "recipient",
        "status",
        "created_at",
    ]
    list_filter = ["notification_type", "status", "created_at"]
    search_fields = ["title", "message"]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "notification_type",
        "recipient",
        "entity_type",
        "entity_id",
        "title",
        "message",
        "status",
        "read_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "notification_type", "recipient", "title", "message")}),
        ("Related Entity", {"fields": ("entity_type", "entity_id")}),
        ("Status", {"fields": ("status", "read_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Notification]:
        """Optimize queryset with select_related for the recipient.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of Notification objects.
        """
        return super().get_queryset(request).select_related("recipient")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding notifications from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since notifications are created by the service layer.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Notification | None = None) -> bool:
        """Disable editing notifications from the admin.

        Args:
            request: The HTTP request.
            obj: The notification instance.

        Returns:
            Always False since notifications are managed by the service layer.
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Notification | None = None) -> bool:
        """Disable deleting notifications from the admin.

        Args:
            request: The HTTP request.
            obj: The notification instance.

        Returns:
            Always False to preserve notification history.
        """
        return False
