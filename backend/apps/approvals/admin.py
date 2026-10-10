"""Django Admin for approvals app."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.http import HttpRequest

from apps.approvals.models import ApprovalDecision, ApprovalRequest

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin, TabularInline
else:
    ModelAdmin = admin.ModelAdmin
    TabularInline = admin.TabularInline


class ApprovalDecisionInline(TabularInline):  # type: ignore[type-arg]
    model = ApprovalDecision
    extra = 0
    readonly_fields = ("id", "decided_by", "decision", "modifications", "comment", "created_at")

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "proposal", "status", "requested_by", "expires_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "summary")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("proposal", "room", "requested_by", "policy_decision")
    inlines = [ApprovalDecisionInline]


@admin.register(ApprovalDecision)
class ApprovalDecisionAdmin(ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "request", "decided_by", "decision", "created_at")
    list_filter = ("decision", "created_at")
    readonly_fields = (
        "id",
        "request",
        "decided_by",
        "decision",
        "modifications",
        "comment",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
