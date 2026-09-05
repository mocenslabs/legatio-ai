"""Agents admin configuration.

This module registers the Agent and AutomationRule models with the Django
admin interface for administrative management.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.agents.models import Agent, AutomationRule


class AutomationRuleInline(admin.TabularInline):
    """Inline for automation rules within an agent.

    Allows managing an agent's automation rules directly from the
    agent's admin page.
    """

    model = AutomationRule
    extra = 0
    fields = [
        "name",
        "trigger_type",
        "action_type",
        "priority",
        "is_active",
    ]
    ordering = ["priority", "-created_at"]


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin interface for Agent model.

    Provides full CRUD operations for administrative management,
    with an inline of automation rules.
    """

    list_display = [
        "name",
        "agent_type",
        "is_active",
        "created_by",
        "created_at",
    ]
    list_filter = ["agent_type", "is_active", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [AutomationRuleInline]

    fieldsets = (
        (None, {"fields": ("id", "name", "description", "agent_type")}),
        ("Configuration", {"fields": ("config",)}),
        ("Status", {"fields": ("is_active", "created_by")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Agent]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of Agent objects.
        """
        return super().get_queryset(request).select_related("created_by")


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    """Admin interface for AutomationRule model.

    Provides full CRUD operations for administrative management
    of automation rules.
    """

    list_display = [
        "name",
        "agent",
        "trigger_type",
        "action_type",
        "priority",
        "is_active",
        "created_at",
    ]
    list_filter = ["trigger_type", "action_type", "is_active", "created_at"]
    search_fields = ["name", "agent__name"]
    ordering = ["priority", "-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "agent", "name")}),
        ("Trigger", {"fields": ("trigger_type", "condition")}),
        ("Action", {"fields": ("action_type", "action_config")}),
        ("Execution", {"fields": ("priority", "is_active", "created_by")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[AutomationRule]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of AutomationRule objects.
        """
        return super().get_queryset(request).select_related("agent", "created_by")
