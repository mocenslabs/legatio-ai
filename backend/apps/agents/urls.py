"""URL configuration for the agents app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.agents.views import AgentViewSet

router = DefaultRouter()
router.register(r"agents", AgentViewSet, basename="agent")

app_name = "agents"

urlpatterns = [
    path("", include(router.urls)),
]
