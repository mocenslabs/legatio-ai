"""Notification API views.

This module provides DRF ViewSets for Notification model operations,
including actions to mark as read and archive.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Notification model.

    Provides list/retrieve operations plus actions to mark as read and
    archive. Notifications are created exclusively by the service layer.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - mark_as_read: Mark a notification as read.
        - archive: Archive a notification.

    Filters:
        - status: Filter by status (query param: ?status=UNREAD)
        - notification_type: Filter by type (query param: ?notification_type=APPROVAL_REQUESTED)
    """

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Notification]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Notification objects.
        """
        queryset = super().get_queryset()

        # Filter by status
        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        # Filter by notification_type
        notification_type = self.request.query_params.get("notification_type")
        if notification_type is not None:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request: Request, pk: str | None = None) -> Response:
        """Mark a notification as read.

        Args:
            request: The HTTP request.
            pk: The notification primary key.

        Returns:
            Response with the updated notification.
        """
        notification = self.get_object()
        notification.mark_as_read()

        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def archive(self, request: Request, pk: str | None = None) -> Response:
        """Archive a notification.

        Args:
            request: The HTTP request.
            pk: The notification primary key.

        Returns:
            Response with the updated notification.
        """
        notification = self.get_object()
        notification.archive()

        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
