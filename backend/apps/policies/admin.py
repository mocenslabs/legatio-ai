"""Policies admin configuration.

This module registers Constitution and PolicyRule models with the Django admin
interface, providing a user-friendly interface for policy management.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.constitutions.models import Constitution
from apps.policies.models import PolicyRule


@admin.register(Constitution)
class ConstitutionAdmin(admin.ModelAdmin):
    """Admin interface for Constitution model.

    Provides list view with filtering, search, and bulk actions.
    """

    list_display = ["name", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "name", "description")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(PolicyRule)
class PolicyRuleAdmin(admin.ModelAdmin):
    """Admin interface for PolicyRule model.

    Provides comprehensive list view with filtering, search, and detailed fieldsets.
    """

    list_display = [
        "name",
        "action_type",
        "risk_level",
        "priority",
        "is_active",
        "constitution",
        "created_at",
    ]
    list_filter = ["action_type", "risk_level", "is_active", "constitution", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["priority", "created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "name", "description")}),
        (
            "Rule Configuration",
            {
                "fields": (
                    "condition",
                    "action_type",
                    "risk_level",
                    "priority",
                )
            },
        ),
        (
            "Approval Settings",
            {
                "fields": ("requires_approval_from",),
                "classes": ("collapse",),
                "description": "Only applicable when action_type is REQUIRE_APPROVAL",
            },
        ),
        (
            "Scope & Status",
            {
                "fields": ("constitution", "is_active"),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[PolicyRule]:
        """Optimize queryset with select_related for constitution.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset.
        """
        return super().get_queryset(request).select_related("constitution")
