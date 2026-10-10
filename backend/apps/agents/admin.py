"""Django Admin configuration for the agents app."""

from django.contrib import admin

from apps.agents.models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin configuration for Agent."""

    list_display = (
        "name",
        "owner",
        "agent_type",
        "status",
        "created_at",
    )
    list_filter = (
        "agent_type",
        "status",
        "created_at",
    )
    search_fields = (
        "name",
        "description",
        "owner__email",
    )
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("owner",)
