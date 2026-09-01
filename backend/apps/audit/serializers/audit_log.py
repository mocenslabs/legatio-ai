"""AuditLog serializer.

This module provides DRF serializers for the AuditLog model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model.

    Audit logs are append-only and managed exclusively by the service
    layer, so all fields are read-only.
    """

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "entity_type",
            "entity_id",
            "actor",
            "old_state",
            "new_state",
            "metadata",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = fields
