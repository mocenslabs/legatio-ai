"""Agent API views.

This module provides DRF ViewSets for Agent model operations, including
lifecycle actions (activate, deactivate).
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

from apps.agents.models import Agent
from apps.agents.serializers import (
    AgentCreateSerializer,
    AgentDetailSerializer,
    AgentSerializer,
)
from apps.agents.services import AgentService, AgentServiceError


class AgentViewSet(viewsets.ModelViewSet):
    """ViewSet for Agent model.

    Provides CRUD operations plus lifecycle actions.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - activate: Activate an agent.
        - deactivate: Deactivate an agent.

    Filters:
        - agent_type: Filter by type (query param: ?agent_type=AUTO_PROPOSER)
        - is_active: Filter by active status (query param: ?is_active=true)
    """

    queryset = Agent.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        """Return the appropriate serializer based on action.

        Returns:
            The serializer class for the current action.
        """
        if self.action == "create":
            return AgentCreateSerializer
        if self.action in ("retrieve", "list"):
            return AgentDetailSerializer
        return AgentSerializer

    def get_queryset(self) -> QuerySet[Agent]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Agent objects.
        """
        queryset = super().get_queryset()

        agent_type = self.request.query_params.get("agent_type")
        if agent_type is not None:
            queryset = queryset.filter(agent_type=agent_type)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new agent via the service layer.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with the created agent.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data

        try:
            agent = AgentService.create_agent(
                name=validated["name"],
                agent_type=validated["agent_type"],
                created_by_id=cast(uuid.UUID, request.user.id),
                description=validated.get("description", ""),
                config=validated.get("config", {}),
            )
        except AgentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = AgentDetailSerializer(agent)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request: Request, pk: str | None = None) -> Response:
        """Activate an agent.

        Args:
            request: The HTTP request.
            pk: The agent primary key.

        Returns:
            Response with the updated agent.
        """
        agent = self.get_object()
        try:
            updated = AgentService.activate_agent(
                agent.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except AgentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgentDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def deactivate(self, request: Request, pk: str | None = None) -> Response:
        """Deactivate an agent.

        Args:
            request: The HTTP request.
            pk: The agent primary key.

        Returns:
            Response with the updated agent.
        """
        agent = self.get_object()
        try:
            updated = AgentService.deactivate_agent(
                agent.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except AgentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgentDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)
