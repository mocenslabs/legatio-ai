"""Constitutions admin configuration.

This module registers the Constitution model with the Django admin
interface, providing a user-friendly interface for constitution management.
"""

from __future__ import annotations

from django.contrib import admin

from apps.constitutions.models import Constitution


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
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
