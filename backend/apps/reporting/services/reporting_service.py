"""Reporting Service layer.

This module provides a service for computing aggregated metrics and
analytics across the system. All methods return plain dictionaries
suitable for serialization and dashboard display.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Count
from django.utils import timezone

from apps.agents.models import Agent, AutomationRule
from apps.agreements.models import Agreement
from apps.audit.models import AuditLog
from apps.negotiations.models import Negotiation
from apps.notifications.models import Notification, NotificationStatus
from apps.proposals.models import Proposal
from apps.scheduling.models import JobStatus, ScheduledJob


class ReportingService:
    """Service layer for reporting and analytics operations.

    Provides aggregated metrics computed on the fly from existing models.
    All methods are read-only and return plain dictionaries.
    """

    @staticmethod
    def get_dashboard_metrics() -> dict[str, Any]:
        """Compute general dashboard metrics for the whole system.

        Returns:
            A dictionary with aggregated counts across all domains:
            proposals, agreements, negotiations, notifications, agents,
            and scheduled jobs.
        """
        return {
            "proposals": ReportingService._get_proposal_counts(),
            "agreements": ReportingService._get_agreement_counts(),
            "negotiations": ReportingService._get_negotiation_counts(),
            "notifications": ReportingService._get_notification_counts(),
            "agents": ReportingService._get_agent_counts(),
            "jobs": ReportingService._get_job_counts(),
            "generated_at": timezone.now().isoformat(),
        }

    @staticmethod
    def _get_proposal_counts() -> dict[str, Any]:
        """Compute proposal counts by status.

        Returns:
            Dictionary with total and per-status proposal counts.
        """
        total = Proposal.objects.count()
        by_status = Proposal.objects.values("status").annotate(count=Count("id"))

        status_counts: dict[str, int] = {}
        for entry in by_status:
            status_counts[entry["status"]] = entry["count"]

        return {
            "total": total,
            "by_status": status_counts,
        }

    @staticmethod
    def _get_agreement_counts() -> dict[str, Any]:
        """Compute agreement counts by status.

        Returns:
            Dictionary with total and per-status agreement counts.
        """
        total = Agreement.objects.count()
        by_status = Agreement.objects.values("status").annotate(count=Count("id"))

        status_counts: dict[str, int] = {}
        for entry in by_status:
            status_counts[entry["status"]] = entry["count"]

        return {
            "total": total,
            "by_status": status_counts,
        }

    @staticmethod
    def _get_negotiation_counts() -> dict[str, Any]:
        """Compute negotiation counts by status.

        Returns:
            Dictionary with total and per-status negotiation counts.
        """
        total = Negotiation.objects.count()
        by_status = Negotiation.objects.values("status").annotate(count=Count("id"))

        status_counts: dict[str, int] = {}
        for entry in by_status:
            status_counts[entry["status"]] = entry["count"]

        return {
            "total": total,
            "by_status": status_counts,
        }

    @staticmethod
    def _get_notification_counts() -> dict[str, Any]:
        """Compute notification counts by status.

        Returns:
            Dictionary with total, unread, and read notification counts.
        """
        total = Notification.objects.count()
        unread = Notification.objects.filter(status=NotificationStatus.UNREAD).count()
        read = Notification.objects.filter(status=NotificationStatus.READ).count()
        archived = Notification.objects.filter(status=NotificationStatus.ARCHIVED).count()

        return {
            "total": total,
            "unread": unread,
            "read": read,
            "archived": archived,
        }

    @staticmethod
    def _get_agent_counts() -> dict[str, Any]:
        """Compute agent and automation rule counts.

        Returns:
            Dictionary with total agents, active agents, and rule counts.
        """
        total_agents = Agent.objects.count()
        active_agents = Agent.objects.filter(is_active=True).count()
        total_rules = AutomationRule.objects.count()
        active_rules = AutomationRule.objects.filter(is_active=True).count()

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_rules": total_rules,
            "active_rules": active_rules,
        }

    @staticmethod
    def _get_job_counts() -> dict[str, Any]:
        """Compute scheduled job counts and success rate.

        Returns:
            Dictionary with total jobs, per-status counts, and success rate.
        """
        total = ScheduledJob.objects.count()
        by_status = ScheduledJob.objects.values("status").annotate(count=Count("id"))

        status_counts: dict[str, int] = {}
        for entry in by_status:
            status_counts[entry["status"]] = entry["count"]

        completed = status_counts.get(JobStatus.COMPLETED, 0)
        failed = status_counts.get(JobStatus.FAILED, 0)
        finished = completed + failed
        success_rate = round((completed / finished) * 100, 2) if finished > 0 else 0.0

        return {
            "total": total,
            "by_status": status_counts,
            "success_rate": success_rate,
        }

    @staticmethod
    def get_activity_feed(limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve recent activity from the audit log.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of recent audit log entries as dictionaries.
        """
        entries = AuditLog.objects.order_by("-created_at")[:limit]

        return [
            {
                "id": str(entry.id),
                "action": entry.action,
                "entity_type": entry.entity_type,
                "entity_id": str(entry.entity_id) if entry.entity_id else None,
                "actor_id": str(entry.actor_id) if entry.actor_id else None,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]
