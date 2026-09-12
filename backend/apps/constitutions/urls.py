"""Constitutions API URLs."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.constitutions.views import ConstitutionViewSet

router = DefaultRouter()
router.register(r"", ConstitutionViewSet, basename="constitution")

urlpatterns = [
    path("", include(router.urls)),
]
