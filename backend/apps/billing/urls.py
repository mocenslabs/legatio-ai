"""Billing URLs."""

from django.urls import path

from apps.billing.views import (
    OrganizationSubscriptionView,
    PlanListView,
    StartFreeSubscriptionView,
)

app_name = "billing"

urlpatterns = [
    path("billing/plans/", PlanListView.as_view(), name="plan-list"),
    path(
        "billing/organizations/<uuid:org_id>/subscription/",
        OrganizationSubscriptionView.as_view(),
        name="org-subscription",
    ),
    path(
        "billing/organizations/<uuid:org_id>/subscription/start-free/",
        StartFreeSubscriptionView.as_view(),
        name="org-start-free",
    ),
]
