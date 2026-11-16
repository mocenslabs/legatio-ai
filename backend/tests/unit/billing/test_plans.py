"""Unit tests for billing plans and limits."""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.billing.models import Plan
from apps.billing.services import (
    ensure_default_plans,
    get_organization_plan,
    increment_usage,
    organization_has_feature,
    organization_within_limit,
    start_free_subscription,
)
from apps.organizations.services import create_organization

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="billing@example.com", password="pass12345")


@pytest.fixture
def org(user):
    return create_organization(name="Billable Co", creator=user)


@pytest.mark.django_db
def test_ensure_default_plans():
    ensure_default_plans()
    codes = set(Plan.objects.values_list("code", flat=True))
    assert {"free", "pro", "business"}.issubset(codes)


@pytest.mark.django_db
def test_start_free_subscription(org):
    sub = start_free_subscription(org)
    assert sub.plan.code == "free"
    assert sub.status == "trialing"
    assert get_organization_plan(org) is not None


@override_settings(BILLING_ENABLED=False)
@pytest.mark.django_db
def test_features_open_when_billing_disabled(org):
    start_free_subscription(org)
    assert organization_has_feature(org, "a2a") is True
    assert organization_within_limit(org, "max_agents", 999) is True


@override_settings(BILLING_ENABLED=True)
@pytest.mark.django_db
def test_limits_enforced_when_billing_enabled(org):
    start_free_subscription(org)
    # free plan max_agents = 3
    assert organization_within_limit(org, "max_agents", 2) is True
    assert organization_within_limit(org, "max_agents", 3) is False
    assert organization_has_feature(org, "audit_export") is False


@pytest.mark.django_db
def test_increment_usage(org):
    r1 = increment_usage(org, "negotiations_started", 1)
    r2 = increment_usage(org, "negotiations_started", 2)
    assert r2.quantity == r1.quantity + 2 or r2.quantity >= 3
