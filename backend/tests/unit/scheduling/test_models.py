"""Unit tests for ScheduledJob model.

Tests cover creation, properties, and string representation.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.scheduling.models import JobStatus, ScheduledJob


@pytest.mark.django_db
class TestScheduledJob:
    """Tests for ScheduledJob model."""

    def test_create_minimal(self) -> None:
        """Verify job can be created with minimal fields."""
        job = ScheduledJob.objects.create(
            name="Test Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        assert job.name == "Test Job"
        assert job.task_name == "apps.test.task"
        assert job.status == JobStatus.PENDING
        assert job.automation_rule is None
        assert job.result is None
        assert job.error == ""

    def test_create_with_all_fields(self) -> None:
        """Verify job can be created with all fields."""
        now = timezone.now()
        job = ScheduledJob.objects.create(
            name="Full Job",
            task_name="apps.test.task",
            status=JobStatus.COMPLETED,
            scheduled_for=now,
            started_at=now,
            finished_at=now + timedelta(seconds=5),
            result={"key": "value"},
            error="",
        )

        assert job.status == JobStatus.COMPLETED
        assert job.result == {"key": "value"}
        assert job.finished_at == now + timedelta(seconds=5)

    def test_str_representation(self) -> None:
        """Verify string representation includes name and status."""
        job = ScheduledJob.objects.create(
            name="My Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        assert str(job) == "My Job (PENDING)"

    def test_default_status_is_pending(self) -> None:
        """Verify default status is PENDING."""
        job = ScheduledJob.objects.create(
            name="Default Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        assert job.status == JobStatus.PENDING

    def test_is_finished_true_when_completed(self) -> None:
        """Verify is_finished returns True when status is COMPLETED."""
        job = ScheduledJob.objects.create(
            name="Completed Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.COMPLETED,
        )

        assert job.is_finished is True

    def test_is_finished_true_when_failed(self) -> None:
        """Verify is_finished returns True when status is FAILED."""
        job = ScheduledJob.objects.create(
            name="Failed Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.FAILED,
        )

        assert job.is_finished is True

    def test_is_finished_false_when_running(self) -> None:
        """Verify is_finished returns False when status is RUNNING."""
        job = ScheduledJob.objects.create(
            name="Running Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.RUNNING,
        )

        assert job.is_finished is False

    def test_succeeded_true_when_completed(self) -> None:
        """Verify succeeded returns True only when status is COMPLETED."""
        completed = ScheduledJob.objects.create(
            name="Completed",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.COMPLETED,
        )
        failed = ScheduledJob.objects.create(
            name="Failed",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.FAILED,
        )

        assert completed.succeeded is True
        assert failed.succeeded is False

    def test_duration_seconds_none_when_not_finished(self) -> None:
        """Verify duration_seconds returns None when job hasn't finished."""
        job = ScheduledJob.objects.create(
            name="Pending Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        assert job.duration_seconds is None

    def test_duration_seconds_calculated(self) -> None:
        """Verify duration_seconds is calculated correctly."""
        now = timezone.now()
        job = ScheduledJob.objects.create(
            name="Timed Job",
            task_name="apps.test.task",
            scheduled_for=now,
            started_at=now,
            finished_at=now + timedelta(seconds=10),
            status=JobStatus.COMPLETED,
        )

        assert job.duration_seconds == 10.0

    def test_ordering_by_scheduled_for_desc(self) -> None:
        """Verify jobs are ordered by scheduled_for descending."""
        now = timezone.now()
        job1 = ScheduledJob.objects.create(
            name="First",
            task_name="apps.test.task",
            scheduled_for=now - timedelta(hours=1),
        )
        job2 = ScheduledJob.objects.create(
            name="Second",
            task_name="apps.test.task",
            scheduled_for=now,
        )

        jobs = list(ScheduledJob.objects.all())

        assert jobs[0].id == job2.id
        assert jobs[1].id == job1.id
