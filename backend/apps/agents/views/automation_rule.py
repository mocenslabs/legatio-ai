"""AutomationRule API views.

This module provides DRF ViewSets for AutomationRule model operations,
including a manual execute action.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.agents.models import AutomationRule
from apps.agents.serializers import (
    AutomationRuleCreateSerializer,
    AutomationRuleSerializer,
    ExecuteRuleSerializer,
)
from apps.agents.services import AutomationService, AutomationServiceError


class AutomationRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for AutomationRule model.

    Provides CRUD operations plus a manual execute action.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - execute: Execute a rule manually against a provided context.

    Filters:
        - agent: Filter by agent ID (query param: ?agent=<uuid>)
        - trigger_type: Filter by trigger type (query param: ?trigger_type=ON_PROPOSAL_CREATED)
        - is_active: Filter by active status (query param: ?is_active=true)
    """

    queryset = AutomationRule.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        """Return the appropriate serializer based on action.

        Returns:
            The serializer class for the current action.
        """
        if self.action == "create":
            return AutomationRuleCreateSerializer
        return AutomationRuleSerializer

    def get_queryset(self) -> QuerySet[AutomationRule]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of AutomationRule objects.
        """
        queryset = super().get_queryset()

        agent_id = self.request.query_params.get("agent")
        if agent_id is not None:
            queryset = queryset.filter(agent_id=agent_id)

        trigger_type = self.request.query_params.get("trigger_type")
        if trigger_type is not None:
            queryset = queryset.filter(trigger_type=trigger_type)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new automation rule via the service layer.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with the created automation rule.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        agent = validated["agent"]

        try:
            rule = AutomationService.create_rule(
                agent_id=agent.id,
                name=validated["name"],
                trigger_type=validated["trigger_type"],
                action_type=validated["action_type"],
                created_by_id=cast(uuid.UUID, request.user.id),
                condition=validated.get("condition", {}),
                action_config=validated.get("action_config", {}),
                priority=validated.get("priority", 100),
            )
        except AutomationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = AutomationRuleSerializer(rule)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def execute(self, request: Request, pk: str | None = None) -> Response:
        """Execute an automation rule manually against a provided context.

        Args:
            request: The HTTP request with the execution context.
            pk: The automation rule primary key.

        Returns:
            Response indicating whether the rule was executed.
        """
        rule = self.get_object()

        input_serializer = ExecuteRuleSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            executed = AutomationService.execute_rule(
                rule_id=rule.id,
                context=input_serializer.validated_data["context"],
            )
        except AutomationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"executed": executed, "rule_id": str(rule.id)},
            status=status.HTTP_200_OK,
        )
