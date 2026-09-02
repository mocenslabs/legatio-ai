"""Agreement serializers.

This module provides DRF serializers for the Agreement model, including
list, detail, create, and action-input variants.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.agreements.models import Agreement
from apps.agreements.serializers.agreement_version import AgreementVersionSerializer


class AgreementSerializer(serializers.ModelSerializer):
    """Serializer for Agreement model (standard representation).

    Provides fields for listing and retrieving agreements. The status
    and created_by fields are read-only as they are managed by the
    service layer.
    """

    class Meta:
        model = Agreement
        fields = [
            "id",
            "title",
            "description",
            "proposal",
            "constitution",
            "status",
            "terms",
            "effective_date",
            "expiration_date",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "effective_date",
            "created_by",
            "created_at",
            "updated_at",
        ]


class AgreementDetailSerializer(serializers.ModelSerializer):
    """Serializer for Agreement model with nested versions.

    Extends the standard representation with version history and
    computed status flags for detailed views.
    """

    versions = AgreementVersionSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_be_activated = serializers.BooleanField(read_only=True)

    class Meta:
        model = Agreement
        fields = [
            "id",
            "title",
            "description",
            "proposal",
            "constitution",
            "status",
            "terms",
            "effective_date",
            "expiration_date",
            "created_by",
            "versions",
            "is_active",
            "is_expired",
            "can_be_activated",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "effective_date",
            "created_by",
            "versions",
            "is_active",
            "is_expired",
            "can_be_activated",
            "created_at",
            "updated_at",
        ]


class AgreementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating agreements.

    Validates input for direct agreement creation. All agreements are
    created in DRAFT status via the service layer.
    """

    class Meta:
        model = Agreement
        fields = [
            "title",
            "description",
            "terms",
            "proposal",
            "constitution",
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


class AgreementAmendSerializer(serializers.Serializer):
    """Serializer for amending an agreement.

    Validates the input for creating an amendment (new version).
    """

    terms = serializers.JSONField(
        help_text="New terms for the agreement.",
    )
    change_reason = serializers.CharField(
        help_text="Description of why the amendment is made.",
    )
    title = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional new title for the agreement.",
    )

    def validate_change_reason(self, value: str) -> str:
        """Validate change_reason is not empty.

        Args:
            value: The change_reason value to validate.

        Returns:
            The validated change_reason.

        Raises:
            serializers.ValidationError: If change_reason is empty.
        """
        if not value.strip():
            raise serializers.ValidationError("change_reason cannot be empty.")
        return value


class GenerateFromProposalSerializer(serializers.Serializer):
    """Serializer for generating an agreement from a proposal.

    Validates the input for the generate_from_proposal action.
    """

    proposal_id = serializers.UUIDField(
        help_text="The UUID of the executed proposal to generate from.",
    )


class TerminateAgreementSerializer(serializers.Serializer):
    """Serializer for terminating an agreement.

    Validates the optional input for the terminate action.
    """

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional reason for termination.",
    )
