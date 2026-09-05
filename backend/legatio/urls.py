"""Legatio project URL configuration.

This module defines the root URL routing for the Legatio project.
"""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Apps
    path("api/policies/", include("apps.policies.urls")),
    path("api/proposals/", include("apps.proposals.urls")),
    path("api/approvals/", include("apps.approvals.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/agreements/", include("apps.agreements.urls")),
    path("api/negotiations/", include("apps.negotiations.urls")),
    path("api/agents/", include("apps.agents.urls")),
    path("api/scheduling/", include("apps.scheduling.urls")),
]
