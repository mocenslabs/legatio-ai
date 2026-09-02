"""Negotiation serializers.

This module provides DRF serializers for the Negotiation model, including
list, detail, create, and action-input variants.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.negotiations.models import Negotiation, NegotiationStatus
from apps.negotiations.serializers.negotiation_offer import NegotiationOfferSerializer


class NegotiationSerializer(serializers.ModelSerializer):
    """Serializer for Negotiation model (standard representation)."""

    class Meta:
        model = Negotiation
        fields = [
            "id",
            "proposal",
            "title",
            "description",
            "status",
            "initiated_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "initiated_by",
            "created_at",
            "updated_at",
        ]


class NegotiationDetailSerializer(serializers.ModelSerializer):
    """Serializer for Negotiation model with nested offers.

    Extends the standard representation with offer history and computed
    status flags for detailed views.
    """

    offers = NegotiationOfferSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_concluded = serializers.BooleanField(read_only=True)

    class Meta:
        model = Negotiation
        fields = [
            "id",
            "proposal",
            "title",
            "description",
            "status",
            "initiated_by",
            "offers",
            "is_active",
            "is_concluded",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "initiated_by",
            "offers",
            "is_active",
            "is_concluded",
            "created_at",
            "updated_at",
        ]


class NegotiationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating negotiations.

    Validates input for negotiation creation. The negotiation is created
    in OPEN status via the service layer.
    """

    class Meta:
        model = Negotiation
        fields = [
            "proposal",
            "title",
            "description",
        ]

    def validate_title(self, value: str) -> str:
        """Validate title is not empty.

        Args:
            value: The title value to validate.

        Returns:
            The validated title.

        Raises:
            serializers.ValidationError: If title is empty.
        """
        if not value.strip():
            raise serializers.ValidationError("title cannot be empty.")
        return value


class MakeOfferSerializer(serializers.Serializer):
    """Serializer for making an offer within a negotiation."""

    terms = serializers.JSONField(
        help_text="Structured JSON terms of the offer.",
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional notes accompanying the offer.",
    )


class ConcludeNegotiationSerializer(serializers.Serializer):
    """Serializer for concluding a negotiation."""

    status = serializers.ChoiceField(
        choices=[
            NegotiationStatus.FAILED,
            NegotiationStatus.CANCELLED,
        ],
        help_text="The target conclusion status (FAILED or CANCELLED).",
    )
