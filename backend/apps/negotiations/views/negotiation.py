"""Negotiation API views.

This module provides DRF ViewSets for Negotiation model operations,
including lifecycle actions (start, make_offer, conclude).
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

from apps.negotiations.models import Negotiation
from apps.negotiations.serializers import (
    ConcludeNegotiationSerializer,
    MakeOfferSerializer,
    NegotiationCreateSerializer,
    NegotiationDetailSerializer,
    NegotiationSerializer,
)
from apps.negotiations.services import (
    InvalidTransitionError,
    NegotiationService,
    NegotiationServiceError,
)


class NegotiationViewSet(viewsets.ModelViewSet):
    """ViewSet for Negotiation model.

    Provides CRUD operations plus lifecycle actions.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - start: Start an open negotiation (OPEN -> IN_PROGRESS).
        - make_offer: Make an offer within the negotiation.
        - conclude: Conclude the negotiation as FAILED or CANCELLED.

    Filters:
        - status: Filter by status (query param: ?status=OPEN)
        - proposal: Filter by proposal ID (query param: ?proposal=<uuid>)
    """

    queryset = Negotiation.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        """Return the appropriate serializer based on action.

        Returns:
            The serializer class for the current action.
        """
        if self.action == "create":
            return NegotiationCreateSerializer
        if self.action in ("retrieve", "list"):
            return NegotiationDetailSerializer
        return NegotiationSerializer

    def get_queryset(self) -> QuerySet[Negotiation]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Negotiation objects.
        """
        queryset = super().get_queryset()

        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        proposal_id = self.request.query_params.get("proposal")
        if proposal_id is not None:
            queryset = queryset.filter(proposal_id=proposal_id)

        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new negotiation via the service layer.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with the created negotiation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        proposal = validated["proposal"]

        try:
            negotiation = NegotiationService.create_negotiation(
                proposal_id=proposal.id,
                title=validated["title"],
                description=validated.get("description", ""),
                initiated_by_id=cast(uuid.UUID, request.user.id),
            )
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = NegotiationDetailSerializer(negotiation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def start(self, request: Request, pk: str | None = None) -> Response:
        """Start an open negotiation.

        Args:
            request: The HTTP request.
            pk: The negotiation primary key.

        Returns:
            Response with the updated negotiation.
        """
        negotiation = self.get_object()
        try:
            updated = NegotiationService.start_negotiation(
                negotiation.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NegotiationDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def make_offer(self, request: Request, pk: str | None = None) -> Response:
        """Make an offer within the negotiation.

        Args:
            request: The HTTP request with offer data.
            pk: The negotiation primary key.

        Returns:
            Response with the created offer.
        """
        negotiation = self.get_object()

        input_serializer = MakeOfferSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            offer = NegotiationService.make_offer(
                negotiation_id=negotiation.id,
                offered_by_id=cast(uuid.UUID, request.user.id),
                terms=input_serializer.validated_data["terms"],
                notes=input_serializer.validated_data.get("notes", ""),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        from apps.negotiations.serializers import NegotiationOfferSerializer

        output_serializer = NegotiationOfferSerializer(offer)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def conclude(self, request: Request, pk: str | None = None) -> Response:
        """Conclude the negotiation as FAILED or CANCELLED.

        Args:
            request: The HTTP request with conclusion status.
            pk: The negotiation primary key.

        Returns:
            Response with the updated negotiation.
        """
        negotiation = self.get_object()

        input_serializer = ConcludeNegotiationSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            updated = NegotiationService.conclude_negotiation(
                negotiation_id=negotiation.id,
                target_status=input_serializer.validated_data["status"],
                actor_id=cast(uuid.UUID, request.user.id),
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NegotiationDetailSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)
