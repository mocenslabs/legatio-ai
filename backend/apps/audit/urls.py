"""Audit API URLs.

This module defines the URL routing for the audit app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.audit.views import AuditLogViewSet

router = DefaultRouter()
router.register(r"", AuditLogViewSet, basename="auditlog")

urlpatterns = router.urls
