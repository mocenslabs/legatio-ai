"""Proposals API URLs.

This module defines the URL routing for the proposals app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.proposals.views import ProposalViewSet

router = DefaultRouter()
router.register(r"", ProposalViewSet, basename="proposal")

urlpatterns = router.urls
