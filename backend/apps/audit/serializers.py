"""
DRF serializers for the audit app.

Source: 05-ROADMAP.md Section 9.5
"""

from typing import Any

from rest_framework import serializers

from apps.audit.models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for AuditEvent (read-only)."""

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "sequence_number",
            "event_type",
            "actor_type",
            "actor_id",
            "entity_type",
            "entity_id",
            "payload",
            "payload_hash",
            "previous_event_hash",
            "event_hash",
            "created_at",
        ]
        read_only_fields = fields


class AuditEventListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Simplified serializer for listing audit events."""

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "sequence_number",
            "event_type",
            "actor_type",
            "entity_type",
            "entity_id",
            "created_at",
        ]
        read_only_fields = fields


class VerificationResultSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for verification results."""

    chain_is_valid = serializers.BooleanField()
    total_events = serializers.IntegerField()
    verified_events = serializers.IntegerField()
    first_invalid_sequence = serializers.IntegerField(allow_null=True, required=False)
    error_message = serializers.CharField(allow_null=True, required=False)
    missing_events = serializers.ListField(child=serializers.IntegerField(), required=False)


class VerificationRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for verification requests."""

    start_sequence = serializers.IntegerField(required=False, min_value=1)
    end_sequence = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that both start and end are provided if one is."""
        start = attrs.get("start_sequence")
        end = attrs.get("end_sequence")

        if (start is None) != (end is None):
            raise serializers.ValidationError(
                "Both start_sequence and end_sequence must be provided together."
            )

        if start is not None and end is not None and start > end:
            raise serializers.ValidationError(
                "start_sequence must be less than or equal to end_sequence."
            )

        return attrs
