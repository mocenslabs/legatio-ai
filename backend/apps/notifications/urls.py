"""Notifications API URLs.

This module defines the URL routing for the notifications app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.notifications.views import NotificationViewSet

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")

urlpatterns = router.urls
