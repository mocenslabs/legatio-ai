"""Audit admin configuration.

This module registers the AuditLog model with the Django admin interface.
Audit logs are read-only since they are append-only records managed by
the service layer.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model (read-only).

    Audit logs are append-only records. This admin provides visibility
    for compliance and debugging but prevents any modification.
    """

    list_display = [
        "action",
        "entity_type",
        "entity_id",
        "actor",
        "created_at",
    ]
    list_filter = ["action", "entity_type", "created_at"]
    search_fields = ["entity_type", "action"]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "action",
        "entity_type",
        "entity_id",
        "actor",
        "old_state",
        "new_state",
        "metadata",
        "ip_address",
        "user_agent",
        "created_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "action", "entity_type", "entity_id", "actor")}),
        ("State Transition", {"fields": ("old_state", "new_state")}),
        ("Context", {"fields": ("metadata", "ip_address", "user_agent")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[AuditLog]:
        """Optimize queryset with select_related for the actor.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of AuditLog objects.
        """
        return super().get_queryset(request).select_related("actor")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding audit logs from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since logs are created by the service layer.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: AuditLog | None = None) -> bool:
        """Disable editing audit logs from the admin.

        Args:
            request: The HTTP request.
            obj: The audit log instance.

        Returns:
            Always False since logs are immutable.
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj: AuditLog | None = None) -> bool:
        """Disable deleting audit logs from the admin.

        Args:
            request: The HTTP request.
            obj: The audit log instance.

        Returns:
            Always False to preserve the audit trail.
        """
        return False
