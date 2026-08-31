"""Proposal API views.

This module provides DRF ViewSets for Proposal model operations,
including lifecycle actions (submit, execute, cancel).
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.proposals.models import Proposal
from apps.proposals.serializers import (
    ProposalCreateSerializer,
    ProposalDetailSerializer,
    ProposalSerializer,
)
from apps.proposals.services import InvalidTransitionError, ProposalService, ProposalServiceError


class ProposalViewSet(viewsets.ModelViewSet):
    # ... (resto del código igual) ...

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Return the appropriate serializer based on action.

        Returns:
            The serializer class for the current action.
        """
        if self.action == "create":
            return ProposalCreateSerializer
        if self.action in ("retrieve", "list"):
            return ProposalDetailSerializer
        return ProposalSerializer

    def get_queryset(self) -> QuerySet[Proposal]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Proposal objects.
        """
        queryset = super().get_queryset()

        # Filter by status
        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Inject the authenticated user as the proposal creator.

        Args:
            serializer: The validated serializer instance.
        """
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request: Request, pk: str | None = None) -> Response:
        """Submit a draft proposal for policy evaluation.

        Args:
            request: The HTTP request.
            pk: The proposal primary key.

        Returns:
            Response with the updated proposal.
        """
        proposal = self.get_object()
        try:
            updated = ProposalService.submit_proposal(proposal.id)
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ProposalServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProposalDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def execute(self, request: Request, pk: str | None = None) -> Response:
        """Execute an approved proposal.

        Args:
            request: The HTTP request.
            pk: The proposal primary key.

        Returns:
            Response with the updated proposal.
        """
        proposal = self.get_object()
        try:
            updated = ProposalService.execute_proposal(proposal.id)
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ProposalServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProposalDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, pk: str | None = None) -> Response:
        """Cancel a proposal.

        Args:
            request: The HTTP request.
            pk: The proposal primary key.

        Returns:
            Response with the updated proposal.
        """
        proposal = self.get_object()
        try:
            updated = ProposalService.cancel_proposal(proposal.id)
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ProposalServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProposalDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)
