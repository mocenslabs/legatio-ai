"""ApprovalRequest API views.

This module provides DRF ViewSets for ApprovalRequest model operations,
including the resolve action for approving/rejecting requests.
"""

from __future__ import annotations

import uuid
from typing import cast

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.approvals.models import ApprovalRequest
from apps.approvals.serializers import ApprovalRequestSerializer, ResolveApprovalSerializer
from apps.proposals.services import InvalidTransitionError, ProposalService, ProposalServiceError


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ApprovalRequest model.

    Provides list/retrieve operations plus the resolve action. Creation,
    update, and deletion are handled exclusively by the service layer.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - resolve: Approve or reject an approval request.

    Filters:
        - status: Filter by status (query param: ?status=PENDING)
        - proposal: Filter by proposal ID (query param: ?proposal=<uuid>)
        - required_role: Filter by role (query param: ?required_role=manager)
    """

    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[ApprovalRequest]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of ApprovalRequest objects.
        """
        queryset = super().get_queryset()

        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        proposal_id = self.request.query_params.get("proposal")
        if proposal_id is not None:
            queryset = queryset.filter(proposal_id=proposal_id)

        required_role = self.request.query_params.get("required_role")
        if required_role is not None:
            queryset = queryset.filter(required_role=required_role)

        return queryset

    @action(detail=True, methods=["post"])
    def resolve(self, request: Request, pk: str | None = None) -> Response:
        """Approve or reject an approval request.

        Args:
            request: The HTTP request with approval decision.
            pk: The approval request primary key.

        Returns:
            Response with the updated approval request.
        """
        approval_request = self.get_object()

        input_serializer = ResolveApprovalSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            updated = ProposalService.resolve_approval(
                approval_request_id=approval_request.id,
                approved=input_serializer.validated_data["approved"],
                decided_by_id=cast(uuid.UUID, request.user.id),
                notes=input_serializer.validated_data.get("notes", ""),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ProposalServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApprovalRequestSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)
