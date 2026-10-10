"""
Views for the agreements app.

Exposes Agreement endpoints for listing, retrieving, signing, and exporting.
All endpoints enforce ownership isolation.
Source: 05-ROADMAP.md Section 9.5
"""

import json
from typing import Any
from uuid import UUID

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.agreements.canonical import to_canonical_json
from apps.agreements.models import Agreement
from apps.agreements.serializers import (
    AgreementListSerializer,
    AgreementSerializer,
    AgreementSignatureSerializer,
    ExportAgreementSerializer,
    SignAgreementSerializer,
)
from apps.agreements.services import sign_agreement, verify_agreement_signature
from core.exceptions import AgreementNotInDraftError, HashMismatchError


class AgreementViewSet(ReadOnlyModelViewSet):  # type: ignore[type-arg]
    """
    ViewSet for Agreement (read-only).

    Endpoints:
        GET /api/v1/agreements/
        GET /api/v1/agreements/{id}/
        POST /api/v1/agreements/{id}/sign
        GET /api/v1/agreements/{id}/canonical
        GET /api/v1/agreements/{id}/signature
        POST /api/v1/agreements/{id}/export
    """

    queryset = Agreement.objects.all()
    serializer_class = AgreementSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[AgreementSerializer] | type[AgreementListSerializer]:
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return AgreementListSerializer
        return AgreementSerializer

    def get_queryset(self) -> Any:
        """Filter agreements by user ownership (via room.user_agent.owner)."""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(room__user_agent__owner=user)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """List all agreements for the user."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a specific agreement."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="sign")
    def sign(self, request: Request, pk: UUID | None = None) -> Response:
        """Sign an agreement with HMAC-SHA256."""
        agreement = self.get_object()
        serializer = SignAgreementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            signature = sign_agreement(
                agreement=agreement,
                user=request.user,
                ip_address=serializer.validated_data.get("ip_address"),
                user_agent_string=serializer.validated_data.get("user_agent_string"),
            )
        except AgreementNotInDraftError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        except HashMismatchError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        agreement.refresh_from_db()
        return Response(
            {
                "agreement": AgreementSerializer(agreement, context={"request": request}).data,
                "signature": AgreementSignatureSerializer(signature).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="canonical")
    def canonical(self, request: Request, pk: UUID | None = None) -> Response:
        """Get the canonical JSON of an agreement."""
        agreement = self.get_object()
        canonical_json = to_canonical_json(agreement.canonical_json)
        return Response(
            {
                "reference_code": agreement.reference_code,
                "canonical_json": canonical_json,
                "canonical_hash": agreement.canonical_hash,
                "status": agreement.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="signature")
    def signature(self, request: Request, pk: UUID | None = None) -> Response:
        """Get the signature details of a signed agreement."""
        agreement = self.get_object()
        if not hasattr(agreement, "signature") or not agreement.signature:
            return Response(
                {"error": "Agreement has not been signed yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        is_verified = verify_agreement_signature(agreement)
        return Response(
            {
                "signature": AgreementSignatureSerializer(agreement.signature).data,
                "is_verified": is_verified,
                "canonical_hash": agreement.canonical_hash,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="export")
    def export(self, request: Request, pk: UUID | None = None) -> HttpResponse:
        """Export an agreement in JSON format."""
        agreement = self.get_object()
        serializer = ExportAgreementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export_data: dict[str, Any] = {
            "reference_code": agreement.reference_code,
            "status": agreement.status,
            "canonical_json": agreement.canonical_json,
            "canonical_hash": agreement.canonical_hash,
            "parties": agreement.parties,
            "terms_summary": agreement.terms_summary,
            "signed_at": (agreement.signed_at.isoformat() if agreement.signed_at else None),
            "created_at": agreement.created_at.isoformat(),
        }

        if hasattr(agreement, "signature") and agreement.signature:
            export_data["signature"] = {
                "algorithm": agreement.signature.signature_algorithm,
                "value": agreement.signature.signature_value,
                "signed_payload_hash": agreement.signature.signed_payload_hash,
                "signer_email": agreement.signature.signer.email,
                "signed_at": agreement.signature.created_at.isoformat(),
                "ip_address": agreement.signature.ip_address,
            }
            export_data["is_verified"] = verify_agreement_signature(agreement)
        else:
            export_data["is_verified"] = False

        json_content = json.dumps(export_data, indent=2, default=str)
        response = HttpResponse(json_content, content_type="application/json")
        response["Content-Disposition"] = (
            f'attachment; filename="agreement_{agreement.reference_code}.json"'
        )
        return response


class VerifyAgreementView(APIView):
    """
    View for verifying an agreement's signature.

    Endpoint: POST /api/v1/agreements/{id}/verify
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: UUID) -> Response:
        """Verify the signature of an agreement."""
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            if user.is_staff:
                agreement = Agreement.objects.get(id=pk)
            else:
                agreement = Agreement.objects.get(
                    id=pk,
                    room__user_agent__owner=user,
                )
        except Agreement.DoesNotExist:
            return Response(
                {"error": "Agreement not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not hasattr(agreement, "signature") or not agreement.signature:
            return Response(
                {"error": "Agreement has not been signed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_verified = verify_agreement_signature(agreement)
        return Response(
            {
                "reference_code": agreement.reference_code,
                "is_verified": is_verified,
                "canonical_hash": agreement.canonical_hash,
                "signature_algorithm": agreement.signature.signature_algorithm,
                "signer_email": agreement.signature.signer.email,
                "signed_at": agreement.signature.created_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
