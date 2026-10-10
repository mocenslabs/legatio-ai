"""Django Admin for negotiations app."""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.negotiations.models import NegotiationMessage, NegotiationRoom


class NegotiationMessageInline(admin.TabularInline):  # type: ignore[type-arg]
    model = NegotiationMessage
    extra = 0
    readonly_fields = (
        "id",
        "sender_type",
        "sender_id",
        "message_type",
        "content",
        "round_number",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(NegotiationRoom)
class NegotiationRoomAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "reference_code",
        "user_agent",
        "external_agent",
        "status",
        "current_round",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("reference_code",)
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user_agent", "external_agent", "constitution")
    inlines = [NegotiationMessageInline]


@admin.register(NegotiationMessage)
class NegotiationMessageAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("room", "sender_type", "message_type", "round_number", "created_at")
    list_filter = ("sender_type", "message_type")
    readonly_fields = (
        "id",
        "room",
        "sender_type",
        "sender_id",
        "message_type",
        "content",
        "round_number",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False
