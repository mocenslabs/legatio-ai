"""
Django Admin configuration for the audit app.
AuditEvent is read-only in the admin interface.
"""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin configuration for AuditEvent (read-only)."""

    list_display = (
        "sequence_number",
        "event_type",
        "actor_type",
        "entity_type",
        "entity_id",
        "created_at",
    )
    list_filter = (
        "event_type",
        "actor_type",
        "entity_type",
        "created_at",
    )
    search_fields = (
        "entity_id",
        "actor_id",
        "event_type",
    )
    readonly_fields = (
        "id",
        "sequence_number",
        "event_type",
        "actor_type",
        "actor_id",
        "entity_type",
        "entity_id",
        "room_id",
        "payload",
        "payload_hash",
        "previous_event_hash",
        "event_hash",
        "correlation_id",
        "created_at",
    )
    ordering = ("-sequence_number",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent adding audit events via admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Prevent changing audit events via admin."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Prevent deleting audit events via admin."""
        return False
