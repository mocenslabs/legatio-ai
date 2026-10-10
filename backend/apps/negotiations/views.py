"""
Views for the negotiations app.

Exposes NegotiationRoom, NegotiationMessage, and related endpoints.
All endpoints enforce ownership isolation.

Source: 05-ROADMAP.md Section 7.3
"""

from typing import Any, cast
from uuid import UUID

from django.db import models
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.negotiations.models import NegotiationRoom
from apps.negotiations.serializers import (
    NegotiationMessageSerializer,
    NegotiationRoomCreateSerializer,
    NegotiationRoomSerializer,
    ProposalSerializer,
)
from core.enums import NegotiationStatus
from core.exceptions import NegotiationStateError
from services.negotiation_engine.orchestrator import NegotiationOrchestrator


class NegotiationRoomViewSet(ModelViewSet):  # type: ignore[type-arg]
    """
    ViewSet for NegotiationRoom CRUD and actions.

    Endpoints:
        GET    /api/v1/negotiations/
        POST   /api/v1/negotiations/
        GET    /api/v1/negotiations/{id}/
        POST   /api/v1/negotiations/{id}/start
        POST   /api/v1/negotiations/{id}/process_round
        GET    /api/v1/negotiations/{id}/messages
        GET    /api/v1/negotiations/{id}/proposals
        POST   /api/v1/negotiations/{id}/cancel
    """

    queryset = NegotiationRoom.objects.all()
    serializer_class = NegotiationRoomSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-created_at"]

    def get_serializer_class(self) -> type:
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return NegotiationRoomCreateSerializer
        return NegotiationRoomSerializer

    def get_queryset(self) -> "models.QuerySet":  # type: ignore[type-arg]
        """Filter negotiations by user ownership (via user_agent)."""
        queryset = super().get_queryset()
        # Filter by user_agent ownership
        return queryset.filter(user_agent__owner=self.request.user)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new NegotiationRoom."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.agents.models import Agent
        from apps.constitutions.models import Constitution

        user_agent = Agent.objects.get(id=serializer.validated_data["user_agent_id"])
        external_agent = Agent.objects.get(id=serializer.validated_data["external_agent_id"])
        constitution = Constitution.objects.get(id=serializer.validated_data["constitution_id"])

        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            title=serializer.validated_data["title"],
            user_instruction=serializer.validated_data["user_instruction"],
            max_rounds=serializer.validated_data.get("max_rounds", 10),
            ttl_hours=serializer.validated_data.get("ttl_hours", 24),
            user=cast(Any, request.user),
        )

        return Response(
            NegotiationRoomSerializer(room, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request: Request, pk: UUID | None = None) -> Response:
        """
        Start the negotiation: transition from PENDING to IN_PROGRESS.

        POST /api/v1/negotiations/{id}/start
        """
        room = self.get_object()

        try:
            orchestrator = NegotiationOrchestrator(room)
            orchestrator.start_negotiation()
        except NegotiationStateError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room.refresh_from_db()
        return Response(
            NegotiationRoomSerializer(room, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="process_round")
    def process_round(self, request: Request, pk: UUID | None = None) -> Response:
        """
        Process a single round of negotiation.

        POST /api/v1/negotiations/{id}/process_round
        """
        room = self.get_object()

        if room.status not in (
            NegotiationStatus.IN_PROGRESS.value,
            NegotiationStatus.IN_PROGRESS,
            NegotiationStatus.AWAITING_APPROVAL.value,
            NegotiationStatus.AWAITING_APPROVAL,
        ):
            return Response(
                {"error": f"Negotiation is not in progress. Status: {room.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            orchestrator = NegotiationOrchestrator(room)
            result = orchestrator.process_round()
        except NegotiationStateError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room.refresh_from_db()

        return Response(
            {
                "room": NegotiationRoomSerializer(room, context={"request": request}).data,
                "round_result": {
                    "round_number": result["round_number"],
                    "proposal": ProposalSerializer(result["proposal"]).data,
                    "policy_decision": {
                        "outcome": result["policy_decision"].outcome,
                        "risk_level": result["policy_decision"].risk_level,
                        "reason": result["policy_decision"].reason,
                        "matched_rules": result["policy_decision"].matched_rules,
                    },
                    "outcome": result["outcome"],
                    "counter_offer": (
                        {
                            "adjustments": result["counter_offer"].adjustments,
                            "reasoning": result["counter_offer"].reasoning,
                        }
                        if result["counter_offer"]
                        else None
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request: Request, pk: UUID | None = None) -> Response:
        """
        List all messages in a negotiation room.

        GET /api/v1/negotiations/{id}/messages
        """
        room = self.get_object()
        messages = room.messages.order_by("round_number", "created_at")
        serializer = NegotiationMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="proposals")
    def proposals(self, request: Request, pk: UUID | None = None) -> Response:
        """
        List all proposals in a negotiation room.

        GET /api/v1/negotiations/{id}/proposals
        """
        room = self.get_object()
        proposals = room.proposals.order_by("round_number", "created_at")
        serializer = ProposalSerializer(proposals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk: UUID | None = None) -> Response:
        """
        Cancel a negotiation.

        POST /api/v1/negotiations/{id}/cancel
        """
        room = self.get_object()

        try:
            room.transition_to(NegotiationStatus.CANCELLED)
        except NegotiationStateError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Audit event
        from apps.audit.services import create_audit_event
        from core.enums import ActorType, EventType

        create_audit_event(
            event_type=EventType.NEGOTIATION_CANCELLED,
            actor_type=ActorType.USER,
            actor_id=request.user.id,
            entity_type="NegotiationRoom",
            entity_id=room.id,
            payload={"reason": "User cancelled"},
        )

        room.refresh_from_db()
        return Response(
            NegotiationRoomSerializer(room, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
