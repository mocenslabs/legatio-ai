"""URL configuration for Legatio AI project."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.api_root import api_root

urlpatterns = [
    path("admin/", admin.site.urls),
    # API discoverability + OpenAPI
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # App routes
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.organizations.urls")),
    path("api/v1/", include("apps.billing.urls")),
    path("api/v1/", include("apps.constitutions.urls")),
    path("api/v1/", include("apps.negotiations.urls")),
    path("api/v1/", include("apps.approvals.urls")),
    path("api/v1/", include("core.health.urls")),
    path("api/v1/", include("apps.agents.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/", include("apps.agreements.urls")),
]
