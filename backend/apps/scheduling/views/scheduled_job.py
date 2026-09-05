"""ScheduledJob API views.

This module provides DRF ViewSets for ScheduledJob model operations.
Scheduled jobs are read-only execution records.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.scheduling.models import ScheduledJob
from apps.scheduling.serializers import ScheduledJobSerializer


class ScheduledJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ScheduledJob model (read-only).

    Provides list and retrieve operations for execution history.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - status: Filter by status (query param: ?status=COMPLETED)
        - task_name: Filter by task name (query param: ?task_name=<name>)
        - automation_rule: Filter by automation rule ID (query param: ?automation_rule=<uuid>)
    """

    queryset = ScheduledJob.objects.all()
    serializer_class = ScheduledJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[ScheduledJob]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of ScheduledJob objects.
        """
        queryset = super().get_queryset()

        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        task_name = self.request.query_params.get("task_name")
        if task_name is not None:
            queryset = queryset.filter(task_name=task_name)

        automation_rule = self.request.query_params.get("automation_rule")
        if automation_rule is not None:
            queryset = queryset.filter(automation_rule_id=automation_rule)

        return queryset
