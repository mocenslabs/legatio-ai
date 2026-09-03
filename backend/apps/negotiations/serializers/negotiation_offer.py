"""NegotiationOffer serializers.

This module provides DRF serializers for the NegotiationOffer model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.negotiations.models import NegotiationOffer


class NegotiationOfferSerializer(serializers.ModelSerializer):
    """Serializer for NegotiationOffer model.

    Offers are managed by the service layer, so most fields are read-only.
    """

    is_pending = serializers.BooleanField(read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)

    class Meta:
        model = NegotiationOffer
        fields = [
            "id",
            "negotiation",
            "offered_by",
            "terms",
            "status",
            "round_number",
            "notes",
            "is_pending",
            "is_resolved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
