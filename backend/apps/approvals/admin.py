"""Approvals admin configuration.

This module registers the ApprovalRequest model with the Django admin interface.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.approvals.models import ApprovalRequest


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    """Admin interface for ApprovalRequest model.

    Provides list view with filtering, search, and read-only fields
    since approval requests are managed by the service layer.
    """

    list_display = [
        "proposal",
        "required_role",
        "status",
        "assigned_to",
        "decided_by",
        "decided_at",
        "created_at",
    ]
    list_filter = ["status", "required_role", "created_at"]
    search_fields = ["proposal__title", "required_role", "notes"]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "proposal",
        "required_role",
        "assigned_to",
        "status",
        "decided_by",
        "decided_at",
        "notes",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "proposal", "required_role", "assigned_to")}),
        ("Decision", {"fields": ("status", "decided_by", "decided_at", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[ApprovalRequest]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of ApprovalRequest objects.
        """
        return super().get_queryset(request).select_related("proposal", "assigned_to", "decided_by")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding approval requests from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since requests are created by the service layer.
        """
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: ApprovalRequest | None = None
    ) -> bool:
        """Disable editing approval requests from the admin.

        Args:
            request: The HTTP request.
            obj: The approval request instance.

        Returns:
            Always False since requests are resolved by the service layer.
        """
        return False
