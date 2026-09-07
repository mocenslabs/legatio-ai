"""Dashboard serializers.

This module provides DRF serializers for dashboard metrics returned
by the ReportingService. These describe the structure of the aggregated
data for API documentation purposes.
"""

from __future__ import annotations

from rest_framework import serializers


class StatusCountSerializer(serializers.Serializer):
    """Serializer for counts by status (proposals, agreements, negotiations)."""

    total = serializers.IntegerField(help_text="Total number of records.")
    by_status = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Counts grouped by status.",
    )


class NotificationCountSerializer(serializers.Serializer):
    """Serializer for notification counts."""

    total = serializers.IntegerField(help_text="Total notifications.")
    unread = serializers.IntegerField(help_text="Unread notifications.")
    read = serializers.IntegerField(help_text="Read notifications.")
    archived = serializers.IntegerField(help_text="Archived notifications.")


class AgentCountSerializer(serializers.Serializer):
    """Serializer for agent and automation rule counts."""

    total_agents = serializers.IntegerField(help_text="Total agents.")
    active_agents = serializers.IntegerField(help_text="Active agents.")
    total_rules = serializers.IntegerField(help_text="Total automation rules.")
    active_rules = serializers.IntegerField(help_text="Active automation rules.")


class JobCountSerializer(serializers.Serializer):
    """Serializer for scheduled job counts and success rate."""

    total = serializers.IntegerField(help_text="Total jobs.")
    by_status = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Counts grouped by status.",
    )
    success_rate = serializers.FloatField(help_text="Success rate percentage.")


class DashboardSerializer(serializers.Serializer):
    """Serializer for the full dashboard metrics."""

    proposals = StatusCountSerializer()
    agreements = StatusCountSerializer()
    negotiations = StatusCountSerializer()
    notifications = NotificationCountSerializer()
    agents = AgentCountSerializer()
    jobs = JobCountSerializer()
    generated_at = serializers.CharField(help_text="ISO timestamp of generation.")
