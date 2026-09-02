"""AgreementVersion serializer.

This module provides DRF serializers for the AgreementVersion model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.agreements.models import AgreementVersion


class AgreementVersionSerializer(serializers.ModelSerializer):
    """Serializer for AgreementVersion model.

    Versions are immutable snapshots created by the service layer,
    so all fields are read-only.
    """

    class Meta:
        model = AgreementVersion
        fields = [
            "id",
            "agreement",
            "version_number",
            "title",
            "terms",
            "change_reason",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields
