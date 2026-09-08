"""Webhook subscription API views.

This module provides DRF ViewSets for WebhookSubscription model operations.
"""

from typing import Any, cast

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from apps.webhooks.models import WebhookSubscription
from apps.webhooks.serializers import WebhookSubscriptionSerializer


class WebhookSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for WebhookSubscription model.

    Provides CRUD operations for managing webhook subscriptions.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - is_active: Filter by active status (query param: ?is_active=true)
    """

    queryset = WebhookSubscription.objects.all()
    serializer_class = WebhookSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[WebhookSubscription]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of WebhookSubscription objects.
        """
        queryset = super().get_queryset()

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Set the created_by field to the current user on creation.

        Args:
            serializer: The validated serializer instance.
        """
        # Cast to WebhookSubscriptionSerializer to satisfy type checker
        # and access the save method with the specific keyword argument.
        ws_serializer = cast(WebhookSubscriptionSerializer, serializer)
        ws_serializer.save(created_by=self.request.user)
