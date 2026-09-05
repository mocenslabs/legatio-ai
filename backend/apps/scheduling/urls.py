"""Scheduling API URLs.

This module defines the URL routing for the scheduling app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.scheduling.views import ScheduledJobViewSet

router = DefaultRouter()
router.register(r"jobs", ScheduledJobViewSet, basename="scheduledjob")

urlpatterns = router.urls
