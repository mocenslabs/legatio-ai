"""
Views for the audit app.

Source: 05-ROADMAP.md Section 9.5
"""

from typing import Any

from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.audit.models import AuditEvent
from apps.audit.serializers import (
    AuditEventListSerializer,
    AuditEventSerializer,
    VerificationRequestSerializer,
)
from apps.audit.verification import (
    detect_missing_events,
    verify_chain_range,
    verify_entity_audit_trail,
    verify_full_chain,
)


class AuditEventViewSet(ReadOnlyModelViewSet):  # type: ignore[type-arg]
    """
    ViewSet for AuditEvent (read-only).

    Endpoints:
        GET /api/v1/audit/events/
        GET /api/v1/audit/events/{id}/
    """

    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["sequence_number"]

    def get_serializer_class(self) -> type[AuditEventSerializer] | type[AuditEventListSerializer]:
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return AuditEventListSerializer
        return AuditEventSerializer

    def get_queryset(self) -> Any:
        """
        Filter audit events by user ownership.
        Users can only see audit events related to their own entities.
        Admins can see all events.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.is_staff:
            return queryset

        # Access related_name='agents' safely via type: ignore
        user_agents = user.agents.all()
        user_agent_ids = [str(agent.id) for agent in user_agents]

        return queryset.filter(
            Q(actor_id=user.id)
            | Q(entity_type="Agent", entity_id__in=user_agent_ids)
            | Q(entity_type="User", entity_id=str(user.id))
        ).distinct()


class EntityAuditTrailView(APIView):
    """
    View for querying audit trail of a specific entity.

    Endpoint:
        GET /api/v1/audit/entities/{entity_type}/{entity_id}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, entity_type: str, entity_id: str) -> Response:
        """Get audit trail for a specific entity."""
        events = AuditEvent.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
        ).order_by("sequence_number")

        serializer = AuditEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyAuditChainView(APIView):
    """
    View for verifying audit chain integrity.

    Endpoint:
        POST /api/v1/audit/verify/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Verify the integrity of the audit hash chain."""
        serializer = VerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start = serializer.validated_data.get("start_sequence")
        end = serializer.validated_data.get("end_sequence")

        if start is not None and end is not None:
            result = verify_chain_range(start, end)
        else:
            result = verify_full_chain()

        missing = detect_missing_events()

        response_data = {
            "chain_is_valid": result.is_valid and not missing,
            "total_events": result.total_events,
            "verified_events": result.verified_events,
            "missing_events": missing,
            "first_invalid_sequence": result.first_invalid_sequence,
            "error_message": result.error_message,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class VerifyEntityAuditView(APIView):
    """
    View for verifying audit trail of a specific entity.

    Endpoint:
        POST /api/v1/audit/entities/{entity_type}/{entity_id}/verify/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, entity_type: str, entity_id: str) -> Response:
        """Verify the audit trail for a specific entity."""
        result = verify_entity_audit_trail(entity_type, entity_id)

        response_data = {
            "chain_is_valid": result.is_valid,
            "total_events": result.total_events,
            "verified_events": result.verified_events,
            "first_invalid_sequence": result.first_invalid_sequence,
            "error_message": result.error_message,
        }

        return Response(response_data, status=status.HTTP_200_OK)
