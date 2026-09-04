"""Agents API URLs.

This module defines the URL routing for the agents app API endpoints.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.agents.views import AgentViewSet, AutomationRuleViewSet

router = DefaultRouter()
router.register(r"rules", AutomationRuleViewSet, basename="automationrule")
router.register(r"", AgentViewSet, basename="agent")

urlpatterns = router.urls
