"""Activity feed serializers.

This module provides DRF serializers for activity feed entries derived
from the audit log.
"""

from __future__ import annotations

from rest_framework import serializers


class ActivityEntrySerializer(serializers.Serializer):
    """Serializer for a single activity feed entry."""

    id = serializers.CharField(help_text="Audit log entry ID.")
    action = serializers.CharField(help_text="The action performed.")
    entity_type = serializers.CharField(help_text="Type of the affected entity.")
    entity_id = serializers.CharField(allow_null=True, help_text="UUID of the affected entity.")
    actor_id = serializers.CharField(
        allow_null=True, help_text="UUID of the user who performed the action."
    )
    created_at = serializers.CharField(help_text="ISO timestamp of the event.")
