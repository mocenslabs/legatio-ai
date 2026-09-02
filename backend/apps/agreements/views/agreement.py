"""Agreement API views.

This module provides DRF ViewSets for Agreement and AgreementVersion model
operations, including lifecycle actions (activate, amend, complete, terminate,
and generate_from_proposal).
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

from apps.agreements.models import Agreement, AgreementVersion
from apps.agreements.serializers import (
    AgreementAmendSerializer,
    AgreementCreateSerializer,
    AgreementDetailSerializer,
    AgreementSerializer,
    AgreementVersionSerializer,
    GenerateFromProposalSerializer,
    TerminateAgreementSerializer,
)
from apps.agreements.services import (
    AgreementService,
    AgreementServiceError,
    InvalidTransitionError,
)


class AgreementViewSet(viewsets.ModelViewSet):
    """ViewSet for Agreement model.

    Provides CRUD operations plus lifecycle actions.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - activate: Activate a draft agreement.
        - amend: Amend an active agreement (creates new version).
        - complete: Complete an active agreement.
        - terminate: Terminate an active agreement.
        - generate_from_proposal: Generate an agreement from an executed proposal.

    Filters:
        - status: Filter by status (query param: ?status=ACTIVE)
        - proposal: Filter by proposal ID (query param: ?proposal=<uuid>)
    """

    queryset = Agreement.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        """Return the appropriate serializer based on action.

        Returns:
            The serializer class for the current action.
        """
        if self.action == "create":
            return AgreementCreateSerializer
        if self.action in ("retrieve", "list"):
            return AgreementDetailSerializer
        return AgreementSerializer

    def get_queryset(self) -> QuerySet[Agreement]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Agreement objects.
        """
        queryset = super().get_queryset()

        # Filter by status
        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        # Filter by proposal
        proposal_id = self.request.query_params.get("proposal")
        if proposal_id is not None:
            queryset = queryset.filter(proposal_id=proposal_id)

        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new agreement via the service layer.

        Uses the service to ensure the initial version and audit log
        are created atomically.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with the created agreement using AgreementDetailSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        proposal_obj = validated.get("proposal")
        constitution_obj = validated.get("constitution")

        agreement = AgreementService.create_agreement(
            title=validated["title"],
            terms=validated.get("terms", {}),
            created_by_id=cast(uuid.UUID, request.user.id),
            description=validated.get("description", ""),
            proposal_id=proposal_obj.id if proposal_obj is not None else None,
            constitution_id=(constitution_obj.id if constitution_obj is not None else None),
        )

        detail_serializer = AgreementDetailSerializer(agreement)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request: Request, pk: str | None = None) -> Response:
        """Activate a draft agreement.

        Args:
            request: The HTTP request.
            pk: The agreement primary key.

        Returns:
            Response with the updated agreement.
        """
        agreement = self.get_object()
        try:
            updated = AgreementService.activate_agreement(
                agreement.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AgreementServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgreementDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def amend(self, request: Request, pk: str | None = None) -> Response:
        """Amend an active agreement, creating a new version.

        Args:
            request: The HTTP request with amendment data.
            pk: The agreement primary key.

        Returns:
            Response with the updated agreement.
        """
        agreement = self.get_object()

        input_serializer = AgreementAmendSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            updated = AgreementService.amend_agreement(
                agreement_id=agreement.id,
                terms=input_serializer.validated_data["terms"],
                change_reason=input_serializer.validated_data["change_reason"],
                actor_id=cast(uuid.UUID, request.user.id),
                title=input_serializer.validated_data.get("title"),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AgreementServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgreementDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def complete(self, request: Request, pk: str | None = None) -> Response:
        """Complete an active agreement.

        Args:
            request: The HTTP request.
            pk: The agreement primary key.

        Returns:
            Response with the updated agreement.
        """
        agreement = self.get_object()
        try:
            updated = AgreementService.complete_agreement(
                agreement.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AgreementServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgreementDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def terminate(self, request: Request, pk: str | None = None) -> Response:
        """Terminate an active agreement.

        Args:
            request: The HTTP request with optional termination reason.
            pk: The agreement primary key.

        Returns:
            Response with the updated agreement.
        """
        agreement = self.get_object()

        input_serializer = TerminateAgreementSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            updated = AgreementService.terminate_agreement(
                agreement.id,
                actor_id=cast(uuid.UUID, request.user.id),
                reason=input_serializer.validated_data.get("reason", ""),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AgreementServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgreementDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def generate_from_proposal(self, request: Request) -> Response:
        """Generate an agreement from an executed proposal.

        Args:
            request: The HTTP request with the proposal_id.

        Returns:
            Response with the created agreement.
        """
        input_serializer = GenerateFromProposalSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            agreement = AgreementService.generate_from_proposal(
                proposal_id=input_serializer.validated_data["proposal_id"],
                actor_id=cast(uuid.UUID, request.user.id),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AgreementServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgreementDetailSerializer(agreement)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AgreementVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AgreementVersion model (read-only).

    Provides list and retrieve operations. Versions are immutable and
    created exclusively by the service layer.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - agreement: Filter by agreement ID (query param: ?agreement=<uuid>)
    """

    queryset = AgreementVersion.objects.all()
    serializer_class = AgreementVersionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[AgreementVersion]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of AgreementVersion objects.
        """
        queryset = super().get_queryset()

        # Filter by agreement
        agreement_id = self.request.query_params.get("agreement")
        if agreement_id is not None:
            queryset = queryset.filter(agreement_id=agreement_id)

        return queryset
