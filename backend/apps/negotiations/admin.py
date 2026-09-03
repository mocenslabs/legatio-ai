"""Negotiations admin configuration.

This module registers the Comment, Negotiation, and NegotiationOffer models
with the Django admin interface. All models are read-only since they are
managed by the service layer, with the exception of comments which allow
deletion for moderation purposes.
"""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.negotiations.models import Comment, Negotiation, NegotiationOffer


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model.

    Comments are created via the API and managed by the service layer.
    This admin provides visibility and allows deletion for moderation.
    """

    list_display = [
        "author",
        "entity_type",
        "entity_id",
        "short_content",
        "is_reply",
        "created_at",
    ]
    list_filter = ["entity_type", "created_at"]
    search_fields = ["content", "author__email"]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "entity_type",
        "entity_id",
        "author",
        "content",
        "parent",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "entity_type", "entity_id", "author", "parent")}),
        ("Content", {"fields": ("content",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Content")
    def short_content(self, obj: Comment) -> str:
        """Return a truncated version of the comment content.

        Args:
            obj: The comment instance.

        Returns:
            First 50 characters of the content.
        """
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    def get_queryset(self, request: HttpRequest) -> QuerySet[Comment]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of Comment objects.
        """
        return super().get_queryset(request).select_related("author", "parent")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding comments from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since comments are created via the API.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Comment | None = None) -> bool:
        """Disable editing comments from the admin.

        Args:
            request: The HTTP request.
            obj: The comment instance.

        Returns:
            Always False since comments are immutable.
        """
        return False


class NegotiationOfferInline(admin.TabularInline):
    """Read-only inline for negotiation offers.

    Offers are managed by the service layer, so this inline is
    read-only for administrative visibility.
    """

    model = NegotiationOffer
    extra = 0
    can_delete = False
    fields = ["round_number", "offered_by", "status", "notes", "created_at"]
    readonly_fields = ["round_number", "offered_by", "status", "notes", "created_at"]

    def has_add_permission(self, request: HttpRequest, obj: Negotiation | None = None) -> bool:
        """Disable adding offers from the admin.

        Args:
            request: The HTTP request.
            obj: The parent negotiation instance.

        Returns:
            Always False to prevent manual offer creation.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Negotiation | None = None) -> bool:
        """Disable editing offers from the admin.

        Args:
            request: The HTTP request.
            obj: The parent negotiation instance.

        Returns:
            Always False to preserve offer integrity.
        """
        return False


@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    """Admin interface for Negotiation model (read-only).

    Negotiations are managed by the service layer with a defined
    lifecycle. This admin provides visibility but prevents modification.
    """

    list_display = [
        "title",
        "proposal",
        "status",
        "initiated_by",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description", "proposal__title"]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "proposal",
        "title",
        "description",
        "status",
        "initiated_by",
        "created_at",
        "updated_at",
    ]
    inlines = [NegotiationOfferInline]

    fieldsets = (
        (None, {"fields": ("id", "title", "description")}),
        ("Relationships", {"fields": ("proposal", "initiated_by")}),
        ("Status", {"fields": ("status",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Negotiation]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of Negotiation objects.
        """
        return super().get_queryset(request).select_related("proposal", "initiated_by")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding negotiations from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since negotiations are created via the service layer.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Negotiation | None = None) -> bool:
        """Disable editing negotiations from the admin.

        Args:
            request: The HTTP request.
            obj: The negotiation instance.

        Returns:
            Always False since negotiations are managed by the service layer.
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Negotiation | None = None) -> bool:
        """Disable deleting negotiations from the admin.

        Args:
            request: The HTTP request.
            obj: The negotiation instance.

        Returns:
            Always False to preserve negotiation history.
        """
        return False


@admin.register(NegotiationOffer)
class NegotiationOfferAdmin(admin.ModelAdmin):
    """Admin interface for NegotiationOffer model (read-only).

    Offers are managed by the service layer. This admin provides
    visibility but prevents any modification.
    """

    list_display = [
        "negotiation",
        "round_number",
        "offered_by",
        "status",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["negotiation__title", "notes"]
    ordering = ["negotiation", "-round_number"]
    readonly_fields = [
        "id",
        "negotiation",
        "offered_by",
        "terms",
        "status",
        "round_number",
        "notes",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {"fields": ("id", "negotiation", "offered_by", "round_number")}),
        ("Offer Details", {"fields": ("terms", "status", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[NegotiationOffer]:
        """Optimize queryset with select_related for foreign keys.

        Args:
            request: The HTTP request.

        Returns:
            Optimized queryset of NegotiationOffer objects.
        """
        return super().get_queryset(request).select_related("negotiation", "offered_by")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding offers from the admin.

        Args:
            request: The HTTP request.

        Returns:
            Always False since offers are created via the service layer.
        """
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: NegotiationOffer | None = None
    ) -> bool:
        """Disable editing offers from the admin.

        Args:
            request: The HTTP request.
            obj: The offer instance.

        Returns:
            Always False since offers are managed by the service layer.
        """
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: NegotiationOffer | None = None
    ) -> bool:
        """Disable deleting offers from the admin.

        Args:
            request: The HTTP request.
            obj: The offer instance.

        Returns:
            Always False to preserve offer history.
        """
        return False
