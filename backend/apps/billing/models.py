"""
Billing models: plans and organization subscriptions.

No payment provider integration yet — structure is ready for Stripe later
via external_* id fields.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from core.enums import PlanInterval, SubscriptionStatus


class Plan(models.Model):
    """
    Commercial plan definition.

    limits example:
      {
        "max_agents": 5,
        "max_negotiations_per_month": 100,
        "max_members": 10
      }

    features example:
      {
        "audit_export": true,
        "a2a": false,
        "priority_support": false
      }
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    interval = models.CharField(
        max_length=20,
        choices=PlanInterval.choices,
        default=PlanInterval.MONTHLY,
    )
    price_cents = models.PositiveIntegerField(
        default=0,
        help_text="List price in cents (display / future billing). 0 = free.",
    )
    currency = models.CharField(max_length=3, default="USD")
    limits = models.JSONField(default=dict, blank=True)
    features = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(
        default=True,
        help_text="If true, plan can be selected by self-serve signup.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=100)
    # Future Stripe (or other) price id
    external_price_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_billing_plan"
        ordering = ["sort_order", "price_cents"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def limit(self, key: str, default: int | None = None) -> int | None:
        value = (self.limits or {}).get(key, default)
        if value is None:
            return default
        return int(value)

    def has_feature(self, key: str) -> bool:
        return bool((self.features or {}).get(key, False))


class OrganizationSubscription(models.Model):
    """
    Current subscription of an organization to a plan.

    One active-ish row per organization (enforced in service layer;
    unique on organization for simplicity in MVP).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIALING,
        db_index=True,
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    # Provider placeholders (Stripe customer / subscription ids)
    external_customer_id = models.CharField(max_length=255, blank=True, default="")
    external_subscription_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_billing_organization_subscription"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.organization_id} → {self.plan.code} ({self.status})"

    @property
    def is_usable(self) -> bool:
        """Whether the org should receive plan benefits right now."""
        return self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        )

    def is_trial_expired(self) -> bool:
        if self.trial_ends_at is None:
            return False
        return timezone.now() >= self.trial_ends_at


class UsageRecord(models.Model):
    """
    Simple monthly usage counters per organization.

    metric examples: negotiations_started, agents_created, api_calls
    period: YYYY-MM
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="usage_records",
    )
    metric = models.CharField(max_length=64, db_index=True)
    period = models.CharField(max_length=7, db_index=True, help_text="YYYY-MM")
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_billing_usage_record"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "metric", "period"],
                name="uniq_usage_org_metric_period",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization_id} {self.metric} {self.period}={self.quantity}"
