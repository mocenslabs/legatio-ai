"""ScheduledJob serializers.

This module provides DRF serializers for the ScheduledJob model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.scheduling.models import ScheduledJob


class ScheduledJobSerializer(serializers.ModelSerializer):
    """Serializer for ScheduledJob model.

    Scheduled jobs are read-only execution records created by the
    system via Celery tasks. All fields are read-only.
    """

    is_finished = serializers.BooleanField(read_only=True)
    succeeded = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = ScheduledJob
        fields = [
            "id",
            "name",
            "task_name",
            "status",
            "automation_rule",
            "scheduled_for",
            "started_at",
            "finished_at",
            "result",
            "error",
            "is_finished",
            "succeeded",
            "duration_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
