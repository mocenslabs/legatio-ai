"""Legatio project URL configuration."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Apps (Agregando v1 para cumplir con ADR-010)
    path("api/v1/constitutions/", include("apps.constitutions.urls")),
    path("api/v1/policies/", include("apps.policies.urls")),
    path("api/v1/proposals/", include("apps.proposals.urls")),
    path("api/v1/approvals/", include("apps.approvals.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/agreements/", include("apps.agreements.urls")),
    path("api/v1/negotiations/", include("apps.negotiations.urls")),
    path("api/v1/agents/", include("apps.agents.urls")),
    path("api/v1/scheduling/", include("apps.scheduling.urls")),
    path("api/v1/reporting/", include("apps.reporting.urls")),
    path("api/v1/webhooks/", include("apps.webhooks.urls")),
]
