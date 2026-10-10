"""
URL configuration for the negotiations app.

Source: 05-ROADMAP.md Section 7.3
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.negotiations import views

router = DefaultRouter()
router.register(r"negotiations", views.NegotiationRoomViewSet, basename="negotiation")

app_name = "negotiations"

urlpatterns = [
    path("", include(router.urls)),
]
