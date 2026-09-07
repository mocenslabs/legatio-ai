"""Reporting API views.

This module exports all views from the reporting app.
"""

from apps.reporting.views.activity import ActivityFeedView
from apps.reporting.views.dashboard import DashboardView

__all__ = ["ActivityFeedView", "DashboardView"]
