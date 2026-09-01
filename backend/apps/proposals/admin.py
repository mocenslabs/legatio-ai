"""Proposals admin configuration.

This module registers the Proposal model with the Django admin interface,
including an inline view of related approval requests.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.approvals.models import ApprovalRequest
from apps.proposals.models import Proposal


class ApprovalRequestInline(admin.TabularInline):
    """Read-only inline for approval requests within a proposal.

    Approval requests are managed by the service layer, so this inline
    is read-only for administrative visibility.
    """

    model = ApprovalRequest
    extra = 0
    can_delete = False
    fields = ["required_role", "assigned_to", "status", "decided_by", "decided_at", "notes"]
    readonly_fields = [
        "required_role",
        "assigned_to",
        "status",
        "decided_by",
        "decided_at",
        "notes",
    ]

    def has_add_permission(self, request: HttpRequest, obj: Proposal | None = None) -> bool:
        """Disable adding approval requests from the admin.

        Args:
            request: The HTTP request.
            obj: The parent proposal instance.

        Returns:
            Always False to prevent manual creation.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Proposal | None = None) -> bool:
        """Disable editing approval requests from the admin.

        Args:
            request: The HTTP request.
            obj: The parent proposal instance.

        Returns:
            Always False to prevent manual edits.
        """
        return False


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Admin interface for Proposal model.

    Provides list view with filtering, search, and a read-only inline
    of related approval requests.
    """

    list_display = [
        "title",
        "action_type",
        "target_resource",
        "status",
        "created_by",
        "created_at",
    ]
    list_filter = ["status", "action_type", "created_at"]
    search_fields = ["title", "description", "action_type", "target_resource"]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "status",
        "policy_decision",
        "created_by",
        "created_at",
        "updated_at",
    ]
    inlines = [ApprovalRequestInline]

    fieldsets = (
        (None, {"fields": ("id", "title", "description")}),
        (
            "Action Details",
            {"fields": ("action_type", "target_resource", "payload", "constitution")},
        ),
        (
            "Status & Decision",
            {"fields": ("status", "policy_decision", "created_by")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Proposal]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of Proposal objects.
        """
        return super().get_queryset(request).select_related("created_by", "constitution")
