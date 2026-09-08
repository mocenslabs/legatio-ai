"""Webhooks API URLs.

This module defines the URL routing for the webhooks app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.webhooks.views import WebhookSubscriptionViewSet

router = DefaultRouter()
router.register(r"subscriptions", WebhookSubscriptionViewSet, basename="webhooksubscription")

urlpatterns = router.urls
