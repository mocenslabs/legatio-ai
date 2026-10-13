"""URL configuration for Legatio AI project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.constitutions.urls")),
    path("api/v1/", include("apps.negotiations.urls")),
    path("api/v1/", include("apps.approvals.urls")),
    path("api/v1/", include("core.health.urls")),
    # Future apps will be added here:
    path("api/v1/", include("apps.agents.urls")),
    # path("api/v1/proposals/", include("apps.proposals.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/", include("apps.agreements.urls")),
]
