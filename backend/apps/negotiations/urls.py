"""Negotiations API URLs.

This module defines the URL routing for the negotiations app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.negotiations.views import (
    CommentViewSet,
    NegotiationOfferViewSet,
    NegotiationViewSet,
)

router = DefaultRouter()
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"offers", NegotiationOfferViewSet, basename="negotiationoffer")
router.register(r"", NegotiationViewSet, basename="negotiation")

urlpatterns = router.urls
