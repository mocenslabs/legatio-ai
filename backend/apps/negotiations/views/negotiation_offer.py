"""NegotiationOffer API views.

This module provides DRF ViewSets for NegotiationOffer model operations,
including actions to accept, reject, and withdraw offers.
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

from apps.negotiations.models import NegotiationOffer
from apps.negotiations.serializers import NegotiationOfferSerializer
from apps.negotiations.services import (
    InvalidTransitionError,
    NegotiationService,
    NegotiationServiceError,
)


class NegotiationOfferViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for NegotiationOffer model.

    Provides list/retrieve operations plus actions to accept, reject,
    and withdraw offers. Offer creation is handled via the Negotiation
    make_offer action.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Actions:
        - accept: Accept a pending offer (concludes negotiation as AGREED).
        - reject: Reject a pending offer.
        - withdraw: Withdraw a pending offer (creator only).

    Filters:
        - negotiation: Filter by negotiation ID (query param: ?negotiation=<uuid>)
        - status: Filter by status (query param: ?status=PENDING)
        - offered_by: Filter by offerer ID (query param: ?offered_by=<uuid>)
    """

    queryset = NegotiationOffer.objects.all()
    serializer_class = NegotiationOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[NegotiationOffer]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of NegotiationOffer objects.
        """
        queryset = super().get_queryset()

        negotiation_id = self.request.query_params.get("negotiation")
        if negotiation_id is not None:
            queryset = queryset.filter(negotiation_id=negotiation_id)

        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        offered_by = self.request.query_params.get("offered_by")
        if offered_by is not None:
            queryset = queryset.filter(offered_by_id=offered_by)

        return queryset

    @action(detail=True, methods=["post"])
    def accept(self, request: Request, pk: str | None = None) -> Response:
        """Accept a pending offer, concluding the negotiation as AGREED.

        Args:
            request: The HTTP request.
            pk: The offer primary key.

        Returns:
            Response with the updated offer.
        """
        offer = self.get_object()
        try:
            updated = NegotiationService.accept_offer(
                offer.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NegotiationOfferSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk: str | None = None) -> Response:
        """Reject a pending offer.

        Args:
            request: The HTTP request.
            pk: The offer primary key.

        Returns:
            Response with the updated offer.
        """
        offer = self.get_object()
        try:
            updated = NegotiationService.reject_offer(
                offer.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NegotiationOfferSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def withdraw(self, request: Request, pk: str | None = None) -> Response:
        """Withdraw a pending offer (creator only).

        Args:
            request: The HTTP request.
            pk: The offer primary key.

        Returns:
            Response with the updated offer.
        """
        offer = self.get_object()
        try:
            updated = NegotiationService.withdraw_offer(
                offer.id, actor_id=cast(uuid.UUID, request.user.id)
            )
        except InvalidTransitionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NegotiationServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NegotiationOfferSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)
