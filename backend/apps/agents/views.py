"""
Views for the agents app.

Exposes Agent list/retrieve/create/update/soft-delete with ownership isolation.
Authenticated users may list:
  - their own agents (owner=user)
  - external/simulated agents (owner is null) for negotiation pairing

Source: MVP Phase B
"""

from typing import Any

from django.db.models import Q, QuerySet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.agents.models import Agent
from apps.agents.serializers import (
    AgentCreateSerializer,
    AgentSerializer,
    AgentUpdateSerializer,
)
from core.enums import AgentType


class AgentViewSet(ModelViewSet):  # type: ignore[type-arg]
    """
    ViewSet for Agent.

    Endpoints:
        GET    /api/v1/agents/
        POST   /api/v1/agents/
        GET    /api/v1/agents/{id}/
        PATCH  /api/v1/agents/{id}/
        DELETE /api/v1/agents/{id}/   (soft delete)
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[Agent]:
        user = self.request.user
        if not user or not user.is_authenticated:
            return Agent.objects.none()

        # Own agents + shared external/simulated (no owner)
        return Agent.objects.filter(
            Q(owner=user)
            | Q(
                owner__isnull=True,
                agent_type__in=[
                    AgentType.EXTERNAL_AGENT,
                    AgentType.SIMULATED,
                ],
            )
        ).order_by("-created_at")

    def get_serializer_class(self) -> Any:
        if self.action == "create":
            return AgentCreateSerializer
        if self.action in ("partial_update", "update"):
            return AgentUpdateSerializer
        return AgentSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.save()
        return Response(
            AgentSerializer(agent, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        agent = self.get_object()
        if agent.owner_id != request.user.id:
            return Response(
                {"error": "You can only update your own agents."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if agent.agent_type != AgentType.USER_AGENT:
            return Response(
                {"error": "Only USER_AGENT instances can be updated via API."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AgentSerializer(agent, context={"request": request}).data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        agent = self.get_object()
        if agent.owner_id != request.user.id:
            return Response(
                {"error": "You can only delete your own agents."},
                status=status.HTTP_403_FORBIDDEN,
            )
        agent.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
