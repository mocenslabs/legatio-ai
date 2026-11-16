"""Billing serializers."""

from rest_framework import serializers

from apps.billing.models import OrganizationSubscription, Plan


class PlanSerializer(serializers.ModelSerializer[Plan]):
    class Meta:
        model = Plan
        fields = [
            "id",
            "code",
            "name",
            "description",
            "interval",
            "price_cents",
            "currency",
            "limits",
            "features",
            "is_public",
            "sort_order",
        ]


class SubscriptionSerializer(serializers.ModelSerializer[OrganizationSubscription]):
    plan = PlanSerializer(read_only=True)
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)

    class Meta:
        model = OrganizationSubscription
        fields = [
            "id",
            "organization_id",
            "plan",
            "status",
            "trial_ends_at",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "created_at",
            "updated_at",
        ]
