"""Scheduling admin configuration.

This module registers the ScheduledJob model with the Django admin
interface for viewing execution history.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.scheduling.models import ScheduledJob


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    """Admin interface for ScheduledJob model (read-only).

    Scheduled jobs are execution records created by the system via
    Celery tasks. This admin provides visibility for debugging and
    monitoring, with deletion allowed for manual cleanup.
    """

    list_display = [
        "name",
        "task_name",
        "status",
        "scheduled_for",
        "started_at",
        "finished_at",
        "duration_display",
    ]
    list_filter = ["status", "task_name", "scheduled_for"]
    search_fields = ["name", "task_name", "error"]
    ordering = ["-scheduled_for"]
    readonly_fields = [
        "id",
        "name",
        "task_name",
        "status",
        "automation_rule",
        "scheduled_for",
        "started_at",
        "finished_at",
        "result",
        "error",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "name", "task_name", "status")}),
        ("Relationships", {"fields": ("automation_rule",)}),
        ("Timing", {"fields": ("scheduled_for", "started_at", "finished_at")}),
        ("Result", {"fields": ("result", "error")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Duration")
    def duration_display(self, obj: ScheduledJob) -> str:
        """Return a formatted duration for display.

        Args:
            obj: The scheduled job instance.

        Returns:
            Formatted duration string, or '-' if not finished.
        """
        duration = obj.duration_seconds
        if duration is None:
            return "-"
        return f"{duration:.2f}s"

    def get_queryset(self, request: HttpRequest) -> QuerySet[ScheduledJob]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of ScheduledJob objects.
        """
        return super().get_queryset(request).select_related("automation_rule")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding jobs from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since jobs are created by the system.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: ScheduledJob | None = None) -> bool:
        """Disable editing jobs from the admin.

        Args:
            request: The HTTP request.
            obj: The scheduled job instance.

        Returns:
            Always False since jobs are immutable execution records.
        """
        return False
