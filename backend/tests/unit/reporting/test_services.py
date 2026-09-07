"""Unit tests for ReportingService.

Tests cover dashboard metrics and activity feed generation.
"""

from __future__ import annotations

import uuid

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.agents.models import ActionType, Agent, AgentType, AutomationRule, TriggerType
from apps.agreements.models import Agreement, AgreementStatus
from apps.audit.models import AuditAction, AuditLog
from apps.negotiations.models import Negotiation, NegotiationStatus
from apps.notifications.models import Notification, NotificationStatus, NotificationType
from apps.proposals.models import Proposal, ProposalStatus
from apps.reporting.services import ReportingService
from apps.scheduling.models import JobStatus, ScheduledJob


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="user@example.com", password="testpass123")


@pytest.fixture
def populated_data(user: User) -> None:
    """Create a variety of records for testing dashboard metrics.

    Args:
        user: The user fixture.
    """
    # Proposals in different statuses
    proposal = Proposal.objects.create(
        title="Draft Proposal",
        action_type="CREATE_PROPOSAL",
        target_resource="proposals",
        created_by=user,
        status=ProposalStatus.DRAFT,
    )
    Proposal.objects.create(
        title="Approved Proposal",
        action_type="CREATE_PROPOSAL",
        target_resource="proposals",
        created_by=user,
        status=ProposalStatus.APPROVED,
    )

    # Agreements in different statuses
    Agreement.objects.create(
        title="Active Agreement",
        terms={},
        created_by=user,
        status=AgreementStatus.ACTIVE,
    )
    Agreement.objects.create(
        title="Draft Agreement",
        terms={},
        created_by=user,
        status=AgreementStatus.DRAFT,
    )

    # Negotiations
    Negotiation.objects.create(
        proposal=proposal,
        title="Test Negotiation",
        initiated_by=user,
        status=NegotiationStatus.IN_PROGRESS,
    )

    # Notifications
    Notification.objects.create(
        notification_type=NotificationType.SYSTEM,
        recipient=user,
        title="Unread Notification",
        status=NotificationStatus.UNREAD,
    )
    Notification.objects.create(
        notification_type=NotificationType.SYSTEM,
        recipient=user,
        title="Read Notification",
        status=NotificationStatus.READ,
    )

    # Agents and rules
    agent = Agent.objects.create(
        name="Active Agent",
        agent_type=AgentType.AUTO_PROPOSER,
        created_by=user,
        is_active=True,
    )
    AutomationRule.objects.create(
        agent=agent,
        name="Active Rule",
        trigger_type=TriggerType.ON_SCHEDULE,
        action_type=ActionType.CREATE_PROPOSAL,
        created_by=user,
        is_active=True,
    )

    # Scheduled jobs
    ScheduledJob.objects.create(
        name="Completed Job",
        task_name="apps.test.task",
        scheduled_for=timezone.now(),
        status=JobStatus.COMPLETED,
    )
    ScheduledJob.objects.create(
        name="Failed Job",
        task_name="apps.test.task",
        scheduled_for=timezone.now(),
        status=JobStatus.FAILED,
    )

    # Audit log entries for activity feed
    AuditLog.objects.create(
        action=AuditAction.PROPOSAL_CREATED,
        entity_type="Proposal",
        entity_id=uuid.uuid4(),
        actor=user,
    )


@pytest.mark.django_db
class TestDashboardMetrics:
    """Tests for ReportingService.get_dashboard_metrics."""

    def test_dashboard_returns_all_sections(self, populated_data: None) -> None:
        """Verify dashboard includes all expected sections."""
        metrics = ReportingService.get_dashboard_metrics()

        assert "proposals" in metrics
        assert "agreements" in metrics
        assert "negotiations" in metrics
        assert "notifications" in metrics
        assert "agents" in metrics
        assert "jobs" in metrics
        assert "generated_at" in metrics

    def test_proposal_counts(self, populated_data: None) -> None:
        """Verify proposal counts by status."""
        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["proposals"]["total"] == 2
        assert metrics["proposals"]["by_status"]["DRAFT"] == 1
        assert metrics["proposals"]["by_status"]["APPROVED"] == 1

    def test_agreement_counts(self, populated_data: None) -> None:
        """Verify agreement counts by status."""
        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["agreements"]["total"] == 2
        assert metrics["agreements"]["by_status"]["ACTIVE"] == 1
        assert metrics["agreements"]["by_status"]["DRAFT"] == 1

    def test_negotiation_counts(self, populated_data: None) -> None:
        """Verify negotiation counts by status."""
        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["negotiations"]["total"] == 1
        assert metrics["negotiations"]["by_status"]["IN_PROGRESS"] == 1

    def test_notification_counts(self, populated_data: None) -> None:
        """Verify notification counts."""
        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["notifications"]["total"] == 2
        assert metrics["notifications"]["unread"] == 1
        assert metrics["notifications"]["read"] == 1

    def test_agent_counts(self, populated_data: None) -> None:
        """Verify agent and rule counts."""
        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["agents"]["total_agents"] == 1
        assert metrics["agents"]["active_agents"] == 1
        assert metrics["agents"]["total_rules"] == 1
        assert metrics["agents"]["active_rules"] == 1

    def test_job_counts_and_success_rate(self, populated_data: None) -> None:
        """Verify job counts and success rate calculation."""
        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["jobs"]["total"] == 2
        assert metrics["jobs"]["by_status"]["COMPLETED"] == 1
        assert metrics["jobs"]["by_status"]["FAILED"] == 1
        assert metrics["jobs"]["success_rate"] == 50.0

    def test_success_rate_zero_when_no_finished_jobs(self, user: User) -> None:
        """Verify success rate is 0 when no jobs have finished."""
        ScheduledJob.objects.create(
            name="Pending Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.PENDING,
        )

        metrics = ReportingService.get_dashboard_metrics()

        assert metrics["jobs"]["success_rate"] == 0.0


@pytest.mark.django_db
class TestActivityFeed:
    """Tests for ReportingService.get_activity_feed."""

    def test_activity_feed_returns_entries(self, populated_data: None) -> None:
        """Verify activity feed returns audit log entries."""
        feed = ReportingService.get_activity_feed(limit=10)

        assert len(feed) >= 1
        assert "id" in feed[0]
        assert "action" in feed[0]
        assert "entity_type" in feed[0]
        assert "created_at" in feed[0]

    def test_activity_feed_respects_limit(self, user: User) -> None:
        """Verify activity feed respects the limit parameter."""
        # Create multiple audit entries
        for i in range(5):
            AuditLog.objects.create(
                action=AuditAction.PROPOSAL_CREATED,
                entity_type="Proposal",
                entity_id=uuid.uuid4(),
                actor=user,
            )

        feed = ReportingService.get_activity_feed(limit=3)

        assert len(feed) == 3

    def test_activity_feed_ordered_by_created_at_desc(self, user: User) -> None:
        """Verify activity feed is ordered by created_at descending."""
        for i in range(3):
            AuditLog.objects.create(
                action=AuditAction.PROPOSAL_CREATED,
                entity_type="Proposal",
                entity_id=uuid.uuid4(),
                actor=user,
            )

        feed = ReportingService.get_activity_feed(limit=10)

        created_times = [entry["created_at"] for entry in feed]
        assert created_times == sorted(created_times, reverse=True)
