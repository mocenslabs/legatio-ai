"""Django Admin for proposals app."""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.proposals.models import CounterProposal, PolicyDecision, Proposal


class CounterProposalInline(admin.TabularInline):  # type: ignore[type-arg]
    model = CounterProposal
    extra = 0
    readonly_fields = ("id", "sender", "adjustments", "reasoning", "created_at")

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


class PolicyDecisionInline(admin.TabularInline):  # type: ignore[type-arg]
    model = PolicyDecision
    extra = 0
    readonly_fields = (
        "id",
        "constitution_version",
        "outcome",
        "risk_level",
        "reason",
        "matched_rules",
        "evaluation_duration_ms",
        "engine_version",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "room",
        "sender",
        "action_type",
        "amount",
        "status",
        "round_number",
        "created_at",
    )
    list_filter = ("status", "action_type", "created_at")
    search_fields = ("id", "action_type")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("room", "sender", "superseded_by")
    inlines = [CounterProposalInline, PolicyDecisionInline]


@admin.register(CounterProposal)
class CounterProposalAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "proposal", "sender", "created_at")
    readonly_fields = (
        "id",
        "proposal",
        "sender",
        "adjustments",
        "reasoning",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(PolicyDecision)
class PolicyDecisionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "proposal",
        "outcome",
        "risk_level",
        "evaluation_duration_ms",
        "created_at",
    )
    list_filter = ("outcome", "risk_level")
    readonly_fields = (
        "id",
        "proposal",
        "constitution_version",
        "outcome",
        "risk_level",
        "reason",
        "matched_rules",
        "evaluation_duration_ms",
        "engine_version",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False
