"""Approvals API URLs.

This module defines the URL routing for the approvals app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.approvals.views import ApprovalRequestViewSet

router = DefaultRouter()
router.register(r"", ApprovalRequestViewSet, basename="approvalrequest")

urlpatterns = router.urls
