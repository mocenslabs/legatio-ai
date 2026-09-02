"""Agreements API URLs.

This module defines the URL routing for the agreements app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.agreements.views import AgreementVersionViewSet, AgreementViewSet

router = DefaultRouter()
router.register(r"versions", AgreementVersionViewSet, basename="agreementversion")
router.register(r"", AgreementViewSet, basename="agreement")

urlpatterns = router.urls
