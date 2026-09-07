"""Reporting API URLs.

This module defines the URL routing for the reporting app API endpoints.
"""

from __future__ import annotations

from django.urls import path

from apps.reporting.views import ActivityFeedView, DashboardView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="reporting-dashboard"),
    path("activity/", ActivityFeedView.as_view(), name="reporting-activity"),
]
