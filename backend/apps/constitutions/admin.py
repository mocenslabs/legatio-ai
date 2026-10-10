"""Django Admin configuration for the constitutions app."""

from django.contrib import admin

from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule


class ConstitutionVersionInline(admin.TabularInline):  # type: ignore[type-arg]
    """Inline admin for ConstitutionVersion."""

    model = ConstitutionVersion
    extra = 0
    readonly_fields = ("created_at",)
    raw_id_fields = ("created_by",)


@admin.register(Constitution)
class ConstitutionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin configuration for Constitution."""

    list_display = (
        "name",
        "agent",
        "status",
        "active_version",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "name",
        "description",
        "agent__name",
    )
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("agent", "active_version")
    inlines = [ConstitutionVersionInline]


class PolicyRuleInline(admin.TabularInline):  # type: ignore[type-arg]
    """Inline admin for PolicyRule."""

    model = PolicyRule
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(ConstitutionVersion)
class ConstitutionVersionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin configuration for ConstitutionVersion."""

    list_display = (
        "constitution",
        "version_number",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "constitution__name",
        "created_by__email",
    )
    readonly_fields = ("created_at",)
    raw_id_fields = ("constitution", "created_by")
    inlines = [PolicyRuleInline]


@admin.register(PolicyRule)
class PolicyRuleAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin configuration for PolicyRule."""

    list_display = (
        "rule_number",
        "name",
        "version",
        "category",
        "action",
        "is_active",
    )
    list_filter = (
        "category",
        "action",
        "is_active",
    )
    search_fields = (
        "name",
        "description",
    )
    readonly_fields = ("created_at",)
    raw_id_fields = ("version",)
