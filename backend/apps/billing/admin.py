"""Admin for billing."""

from django.contrib import admin

from apps.billing.models import OrganizationSubscription, Plan, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "code",
        "name",
        "price_cents",
        "interval",
        "is_active",
        "is_public",
        "sort_order",
    )
    list_filter = ("is_active", "is_public", "interval")
    search_fields = ("code", "name")
    prepopulated_fields = {"code": ("name",)}


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "organization",
        "plan",
        "status",
        "trial_ends_at",
        "current_period_end",
    )
    list_filter = ("status", "plan")
    raw_id_fields = ("organization", "plan")
    search_fields = (
        "organization__name",
        "organization__slug",
        "external_customer_id",
    )


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("organization", "metric", "period", "quantity", "updated_at")
    list_filter = ("metric", "period")
    raw_id_fields = ("organization",)
