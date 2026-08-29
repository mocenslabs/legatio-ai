"""Policies API URLs.

This module defines the URL routing for the policies app API endpoints.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.policies.views import (
    ConstitutionViewSet,
    PolicyEvaluationView,
    PolicyRuleViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"constitutions", ConstitutionViewSet, basename="constitution")
router.register(r"rules", PolicyRuleViewSet, basename="policyrule")

# URL patterns
urlpatterns = [
    path("", include(router.urls)),
    path("evaluate/", PolicyEvaluationView.as_view(), name="policy-evaluate"),
]
