"""Constitution API views.

This module provides DRF ViewSets for Constitution model CRUD operations.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.constitutions.models import Constitution
from apps.policies.serializers import ConstitutionSerializer


class ConstitutionViewSet(viewsets.ModelViewSet[Constitution]):
    """ViewSet for Constitution model.

    Provides list, retrieve, create, update, and delete operations
    for constitution management.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - is_active: Filter by active status (query param: ?is_active=true)
    """

    queryset = Constitution.objects.all()
    serializer_class = ConstitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Constitution]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Constitution objects.
        """
        queryset = super().get_queryset()

        # Filter by is_active if provided
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset
