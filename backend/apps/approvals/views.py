"""
Views for the approvals app.

Exposes ApprovalRequest and ApprovalDecision endpoints.
All endpoints enforce ownership isolation via room.user_agent.owner.

Source: 05-ROADMAP.md Section 8.5
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.approvals.models import ApprovalRequest
from apps.approvals.serializers import (
    ApprovalDecisionCreateSerializer,
    ApprovalDecisionSerializer,
    ApprovalRequestListSerializer,
    ApprovalRequestSerializer,
)
from apps.approvals.services import process_approval_decision
from core.enums import ApprovalStatus
from core.exceptions import (
    ApprovalAlreadyDecidedError,
    ApprovalExpiredError,
    ApprovalUnauthorizedError,
)


class ApprovalRequestViewSet(ReadOnlyModelViewSet):  # type: ignore[type-arg]
    """
    Read-only ViewSet for ApprovalRequest.

    Endpoints:
        GET /api/v1/approvals/
        GET /api/v1/approvals/pending/
        GET /api/v1/approvals/{id}/
    """

    queryset = ApprovalRequest.objects.select_related(
        "proposal",
        "policy_decision",
        "room",
        "requested_by",
    ).prefetch_related("decisions")
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type:
        if self.action == "list" or self.action == "pending":
            return ApprovalRequestListSerializer
        return ApprovalRequestSerializer

    def get_queryset(self) -> Any:
        """Restrict to approvals owned by the authenticated user."""
        queryset = super().get_queryset()
        return queryset.filter(room__user_agent__owner=self.request.user)

    @action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request: Request) -> Response:
        """List pending approval requests for the current user."""
        queryset = self.get_queryset().filter(status=ApprovalStatus.PENDING)
        serializer = ApprovalRequestListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApprovalDecisionView(APIView):
    """
    Base view for processing approval decisions.

    Subclasses map URL path → ApprovalStatus.
    """

    permission_classes = [IsAuthenticated]
    decision_status: ApprovalStatus = ApprovalStatus.APPROVED

    def post(self, request: Request, pk: UUID) -> Response:
        """Process an approval decision for the given request id."""
        # Check authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            approval_request = ApprovalRequest.objects.select_related(
                "room__user_agent",
                "proposal",
            ).get(
                id=pk,
                room__user_agent__owner=request.user,
            )
        except ApprovalRequest.DoesNotExist:
            return Response(
                {"error": "Approval request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Inject decision from path so body only needs comment/modifications
        data = {
            **getattr(request, "data", {}),
            "decision": self.decision_status.value,
        }
        serializer = ApprovalDecisionCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            approval_decision = process_approval_decision(
                request=approval_request,
                user=request.user,
                decision=self.decision_status,
                modifications=serializer.validated_data.get("modifications"),
                comment=serializer.validated_data.get("comment") or "",
            )
        except ApprovalAlreadyDecidedError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        except ApprovalExpiredError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_410_GONE)
        except ApprovalUnauthorizedError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ApprovalDecisionSerializer(approval_decision).data,
            status=status.HTTP_201_CREATED,
        )


class ApproveView(ApprovalDecisionView):
    """POST /api/v1/approvals/{id}/approve/"""

    decision_status = ApprovalStatus.APPROVED


class RejectView(ApprovalDecisionView):
    """POST /api/v1/approvals/{id}/reject/"""

    decision_status = ApprovalStatus.REJECTED


class ModifyView(ApprovalDecisionView):
    """POST /api/v1/approvals/{id}/modify/"""

    decision_status = ApprovalStatus.MODIFIED
