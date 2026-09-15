"""Constitution API views.

This module provides DRF ViewSets for Constitution model CRUD operations.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.constitutions.models import Constitution
from apps.constitutions.serializers import ConstitutionSerializer


class ConstitutionViewSet(viewsets.ModelViewSet):
    """ViewSet for Constitution model.

    Provides list, retrieve, create, update, and delete operations
    for constitution management.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    User Scoping:
        - Users can only see and modify their own constitutions.
        - The user field is automatically assigned on creation.

    Filters:
        - is_active: Filter by active status (query param: ?is_active=true)
    """

    serializer_class = ConstitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Constitution]:
        """Filter queryset to only show user's own constitutions.

        Returns:
            Filtered queryset of Constitution objects owned by the current user.
        """
        user = self.request.user

        # Narrow type for mypy: if not authenticated, return empty queryset
        if not user.is_authenticated:
            return Constitution.objects.none()

        # Now mypy knows 'user' is a valid User instance
        queryset = Constitution.objects.filter(user=user)

        # Filter by is_active if provided
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def perform_create(self, serializer: ConstitutionSerializer) -> None:  # type: ignore[override]
        """Assign the authenticated user as the owner on creation.

        Args:
            serializer: The serializer instance.
        """
        # CRITICAL: Assign the authenticated user as the owner
        serializer.save(user=self.request.user)
