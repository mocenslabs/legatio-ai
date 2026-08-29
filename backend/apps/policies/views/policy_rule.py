"""PolicyRule API views.

This module provides DRF ViewSets for PolicyRule model CRUD operations.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.policies.models import PolicyRule
from apps.policies.serializers import PolicyRuleSerializer


class PolicyRuleViewSet(viewsets.ModelViewSet[PolicyRule]):
    """ViewSet for PolicyRule model.

    Provides list, retrieve, create, update, and delete operations
    for policy rule management.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - is_active: Filter by active status (query param: ?is_active=true)
        - constitution: Filter by constitution ID (query param: ?constitution=<uuid>)
        - action_type: Filter by action type (query param: ?action_type=DENY)
        - risk_level: Filter by risk level (query param: ?risk_level=HIGH)
    """

    queryset = PolicyRule.objects.all()
    serializer_class = PolicyRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[PolicyRule]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of PolicyRule objects.
        """
        queryset = super().get_queryset()

        # Filter by is_active
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by constitution
        constitution_id = self.request.query_params.get("constitution")
        if constitution_id is not None:
            queryset = queryset.filter(constitution_id=constitution_id)

        # Filter by action_type
        action_type = self.request.query_params.get("action_type")
        if action_type is not None:
            queryset = queryset.filter(action_type=action_type)

        # Filter by risk_level
        risk_level = self.request.query_params.get("risk_level")
        if risk_level is not None:
            queryset = queryset.filter(risk_level=risk_level)

        return queryset
