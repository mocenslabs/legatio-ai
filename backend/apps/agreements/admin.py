"""Agreements admin configuration.

This module registers the Agreement and AgreementVersion models with the
Django admin interface. Agreements are editable for administrative
management, while versions are read-only immutable snapshots.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.agreements.models import Agreement, AgreementVersion


class AgreementVersionInline(admin.TabularInline):
    """Read-only inline for agreement versions.

    Versions are immutable snapshots managed by the service layer,
    so this inline is read-only for administrative visibility.
    """

    model = AgreementVersion
    extra = 0
    can_delete = False
    fields = ["version_number", "title", "change_reason", "created_by", "created_at"]
    readonly_fields = [
        "version_number",
        "title",
        "change_reason",
        "created_by",
        "created_at",
    ]

    def has_add_permission(self, request: HttpRequest, obj: Agreement | None = None) -> bool:
        """Disable adding versions from the admin.

        Args:
            request: The HTTP request.
            obj: The parent agreement instance.

        Returns:
            Always False to prevent manual version creation.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Agreement | None = None) -> bool:
        """Disable editing versions from the admin.

        Args:
            request: The HTTP request.
            obj: The parent agreement instance.

        Returns:
            Always False to preserve version immutability.
        """
        return False


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    """Admin interface for Agreement model.

    Provides full CRUD operations for administrative management,
    with a read-only inline of version history.
    """

    list_display = [
        "title",
        "status",
        "proposal",
        "constitution",
        "effective_date",
        "expiration_date",
        "created_by",
        "created_at",
    ]
    list_filter = ["status", "created_at", "effective_date"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [AgreementVersionInline]

    fieldsets = (
        (None, {"fields": ("id", "title", "description")}),
        (
            "Relationships",
            {"fields": ("proposal", "constitution", "created_by")},
        ),
        (
            "Status & Dates",
            {"fields": ("status", "effective_date", "expiration_date")},
        ),
        ("Terms", {"fields": ("terms",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Agreement]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of Agreement objects.
        """
        return (
            super().get_queryset(request).select_related("proposal", "constitution", "created_by")
        )


@admin.register(AgreementVersion)
class AgreementVersionAdmin(admin.ModelAdmin):
    """Admin interface for AgreementVersion model (read-only).

    Versions are immutable snapshots created by the service layer.
    This admin provides visibility but prevents any modification.
    """

    list_display = [
        "agreement",
        "version_number",
        "title",
        "change_reason",
        "created_by",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["title", "change_reason", "agreement__title"]
    ordering = ["agreement", "-version_number"]
    readonly_fields = [
        "id",
        "agreement",
        "version_number",
        "title",
        "terms",
        "change_reason",
        "created_by",
        "created_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "agreement", "version_number")}),
        ("Snapshot", {"fields": ("title", "terms")}),
        ("Change Info", {"fields": ("change_reason", "created_by")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[AgreementVersion]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of AgreementVersion objects.
        """
        return super().get_queryset(request).select_related("agreement", "created_by")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding versions from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since versions are created by the service layer.
        """
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: AgreementVersion | None = None
    ) -> bool:
        """Disable editing versions from the admin.

        Args:
            request: The HTTP request.
            obj: The agreement version instance.

        Returns:
            Always False to preserve version immutability.
        """
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: AgreementVersion | None = None
    ) -> bool:
        """Disable deleting versions from the admin.

        Args:
            request: The HTTP request.
            obj: The agreement version instance.

        Returns:
            Always False to preserve version history.
        """
        return False
