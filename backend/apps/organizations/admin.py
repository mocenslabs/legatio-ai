"""Admin for organizations."""

from django.contrib import admin

from apps.organizations.models import Organization, OrganizationMembership


class MembershipInline(admin.TabularInline):  # type: ignore[type-arg]
    model = OrganizationMembership
    extra = 0
    raw_id_fields = ("user", "invited_by")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "slug", "status", "created_at", "deleted_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("organization", "user", "role", "created_at")
    list_filter = ("role",)
    raw_id_fields = ("organization", "user", "invited_by")
