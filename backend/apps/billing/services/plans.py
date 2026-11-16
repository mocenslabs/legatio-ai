"""Plan and usage helpers (no payment provider)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.billing.models import OrganizationSubscription, Plan, UsageRecord
from core.enums import PlanInterval, SubscriptionStatus

DEFAULT_PLANS: list[dict[str, Any]] = [
    {
        "code": "free",
        "name": "Free",
        "description": "Personal / evaluation use",
        "interval": PlanInterval.MONTHLY,
        "price_cents": 0,
        "limits": {
            "max_agents": 3,
            "max_negotiations_per_month": 20,
            "max_members": 3,
        },
        "features": {
            "audit_export": False,
            "a2a": False,
            "priority_support": False,
        },
        "sort_order": 10,
    },
    {
        "code": "pro",
        "name": "Pro",
        "description": "Small teams",
        "interval": PlanInterval.MONTHLY,
        "price_cents": 4900,
        "limits": {
            "max_agents": 25,
            "max_negotiations_per_month": 500,
            "max_members": 20,
        },
        "features": {
            "audit_export": True,
            "a2a": True,
            "priority_support": False,
        },
        "sort_order": 20,
    },
    {
        "code": "business",
        "name": "Business",
        "description": "Companies with compliance needs",
        "interval": PlanInterval.MONTHLY,
        "price_cents": 19900,
        "limits": {
            "max_agents": 200,
            "max_negotiations_per_month": 5000,
            "max_members": 100,
        },
        "features": {
            "audit_export": True,
            "a2a": True,
            "priority_support": True,
        },
        "sort_order": 30,
    },
]


def billing_enabled() -> bool:
    return bool(getattr(settings, "BILLING_ENABLED", False))


def ensure_default_plans() -> list[Plan]:
    """Idempotent seed of catalog plans."""
    created: list[Plan] = []
    for spec in DEFAULT_PLANS:
        plan, was_created = Plan.objects.update_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "description": spec["description"],
                "interval": spec["interval"],
                "price_cents": spec["price_cents"],
                "limits": spec["limits"],
                "features": spec["features"],
                "sort_order": spec["sort_order"],
                "is_public": True,
                "is_active": True,
            },
        )
        if was_created:
            created.append(plan)
    return created


@transaction.atomic
def start_free_subscription(organization: Any, *, trial_days: int = 14) -> OrganizationSubscription:
    """Attach the free plan (trialing) to an organization if none exists."""
    ensure_default_plans()
    existing = OrganizationSubscription.objects.filter(organization=organization).first()
    if existing:
        return existing

    plan = Plan.objects.get(code="free")
    now = timezone.now()
    return OrganizationSubscription.objects.create(
        organization=organization,
        plan=plan,
        status=SubscriptionStatus.TRIALING,
        trial_ends_at=now + timedelta(days=trial_days),
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )


def get_organization_plan(organization: Any) -> Plan | None:
    sub = getattr(organization, "subscription", None)
    if sub is None:
        try:
            sub = OrganizationSubscription.objects.select_related("plan").get(
                organization=organization
            )
        except OrganizationSubscription.DoesNotExist:
            return None
    if not sub.is_usable:
        return None
    return sub.plan


def organization_has_feature(organization: Any, feature: str) -> bool:
    if not billing_enabled():
        # When billing is off, all features are available (dev / early MVP).
        return True
    plan = get_organization_plan(organization)
    if plan is None:
        return False
    return plan.has_feature(feature)


def organization_within_limit(organization: Any, limit_key: str, current_count: int) -> bool:
    """
    Return True if current_count is still within plan limit.
    Missing limit key => unlimited.
    """
    if not billing_enabled():
        return True
    plan = get_organization_plan(organization)
    if plan is None:
        return False
    max_value = plan.limit(limit_key)
    if max_value is None:
        return True
    return current_count < max_value


def _current_period() -> str:
    return timezone.now().strftime("%Y-%m")


def increment_usage(organization: Any, metric: str, amount: int = 1) -> UsageRecord:
    period = _current_period()
    record, _ = UsageRecord.objects.get_or_create(
        organization=organization,
        metric=metric,
        period=period,
        defaults={"quantity": 0},
    )
    UsageRecord.objects.filter(pk=record.pk).update(
        quantity=F("quantity") + amount,
        updated_at=timezone.now(),
    )
    record.refresh_from_db()
    return record
