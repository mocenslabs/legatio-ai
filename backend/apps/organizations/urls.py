"""URL configuration for organizations."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.organizations.views import OrganizationViewSet

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")

app_name = "organizations"

urlpatterns = [
    path("", include(router.urls)),
]
