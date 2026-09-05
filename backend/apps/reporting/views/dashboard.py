"""Dashboard API views.

This module provides the API view for system-wide dashboard metrics.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reporting.serializers import DashboardSerializer
from apps.reporting.services import ReportingService


class DashboardView(APIView):
    """API view for system-wide dashboard metrics.

    Returns aggregated counts across proposals, agreements, negotiations,
    notifications, agents, and scheduled jobs.

    Permissions:
        - IsAuthenticated: Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DashboardSerializer)
    def get(self, request: Request) -> Response:
        """Return dashboard metrics.

        Args:
            request: The HTTP request.

        Returns:
            Response with aggregated dashboard metrics.
        """
        data = ReportingService.get_dashboard_metrics()
        serializer = DashboardSerializer(data)
        return Response(serializer.data)
