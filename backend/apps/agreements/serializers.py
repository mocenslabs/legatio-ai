"""
DRF serializers for the agreements app.

Handles validation and serialization for Agreement and AgreementSignature.
Source: 05-ROADMAP.md Section 9.5
"""

from rest_framework import serializers

from apps.agreements.models import Agreement, AgreementSignature


class AgreementSignatureSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for AgreementSignature (read-only)."""

    signer_email = serializers.CharField(source="signer.email", read_only=True)

    class Meta:
        model = AgreementSignature
        fields = [
            "id",
            "agreement",
            "signer",
            "signer_email",
            "signature_algorithm",
            "signature_value",
            "signed_payload_hash",
            "ip_address",
            "user_agent_string",
            "created_at",
        ]
        read_only_fields = fields


class AgreementSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for Agreement."""

    room_reference_code = serializers.CharField(source="room.reference_code", read_only=True)
    proposal_amount = serializers.SerializerMethodField()
    proposal_action_type = serializers.SerializerMethodField()
    constitution_version_number = serializers.SerializerMethodField()
    signature = AgreementSignatureSerializer(read_only=True)
    is_signed = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = Agreement
        fields = [
            "id",
            "reference_code",
            "room",
            "room_reference_code",
            "proposal",
            "proposal_amount",
            "proposal_action_type",
            "constitution_version",
            "constitution_version_number",
            "status",
            "canonical_json",
            "canonical_hash",
            "parties",
            "terms_summary",
            "signed_at",
            "executed_at",
            "voided_at",
            "signature",
            "is_signed",
            "is_verified",
            "created_at",
        ]
        read_only_fields = fields

    def get_proposal_amount(self, obj: Agreement) -> str | None:
        """Return proposal amount."""
        if obj.proposal.amount:
            return str(obj.proposal.amount)
        return None

    def get_proposal_action_type(self, obj: Agreement) -> str:
        """Return proposal action type."""
        return obj.proposal.action_type

    def get_constitution_version_number(self, obj: Agreement) -> int:
        """Return constitution version number."""
        return obj.constitution_version.version_number

    def get_is_signed(self, obj: Agreement) -> bool:
        """Check if agreement is signed."""
        return obj.status in ["SIGNED", "EXECUTED"]

    def get_is_verified(self, obj: Agreement) -> bool:
        """Check if signature is verified."""
        if not self.get_is_signed(obj):
            return False
        if not hasattr(obj, "signature") or not obj.signature:
            return False
        from apps.agreements.services import verify_agreement_signature

        return verify_agreement_signature(obj)


class AgreementListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Simplified serializer for listing agreements."""

    room_reference_code = serializers.CharField(source="room.reference_code", read_only=True)
    proposal_amount = serializers.SerializerMethodField()
    is_signed = serializers.SerializerMethodField()

    class Meta:
        model = Agreement
        fields = [
            "id",
            "reference_code",
            "room_reference_code",
            "proposal_amount",
            "status",
            "terms_summary",
            "signed_at",
            "is_signed",
            "created_at",
        ]
        read_only_fields = fields

    def get_proposal_amount(self, obj: Agreement) -> str | None:
        """Return proposal amount."""
        if obj.proposal.amount:
            return str(obj.proposal.amount)
        return None

    def get_is_signed(self, obj: Agreement) -> bool:
        """Check if agreement is signed."""
        return obj.status in ["SIGNED", "EXECUTED"]


class SignAgreementSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for signing an agreement."""

    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    user_agent_string = serializers.CharField(
        required=False, allow_blank=True, max_length=255, default=""
    )


class ExportAgreementSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for exporting an agreement."""

    format = serializers.ChoiceField(
        choices=["json"],
        default="json",
    )
