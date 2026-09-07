"""Activity feed API views.

This module provides the API view for the recent activity feed derived
from the audit log.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reporting.serializers import ActivityEntrySerializer
from apps.reporting.services import ReportingService

# Maximum number of activity entries that can be requested
MAX_ACTIVITY_LIMIT = 100

# Default number of activity entries
DEFAULT_ACTIVITY_LIMIT = 20


class ActivityFeedView(APIView):
    """API view for the recent activity feed.

    Returns recent audit log entries as an activity feed. Supports a
    `limit` query parameter to control the number of entries returned.

    Permissions:
        - IsAuthenticated: Requires authentication.

    Query Parameters:
        - limit: Number of entries to return (1-100, default 20).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="limit",
                type=int,
                description="Number of entries to return (1-100, default 20).",
            ),
        ],
        responses=ActivityEntrySerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        """Return the recent activity feed.

        Args:
            request: The HTTP request.

        Returns:
            Response with recent activity entries.
        """
        limit = self._parse_limit(request)
        entries = ReportingService.get_activity_feed(limit=limit)
        serializer = ActivityEntrySerializer(entries, many=True)
        return Response(serializer.data)

    def _parse_limit(self, request: Request) -> int:
        """Parse and validate the limit query parameter.

        Args:
            request: The HTTP request.

        Returns:
            A valid limit between 1 and MAX_ACTIVITY_LIMIT.
        """
        raw_limit = request.query_params.get("limit", str(DEFAULT_ACTIVITY_LIMIT))
        try:
            limit = int(raw_limit)
        except (ValueError, TypeError):
            limit = DEFAULT_ACTIVITY_LIMIT

        return max(1, min(limit, MAX_ACTIVITY_LIMIT))
