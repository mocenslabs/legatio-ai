"""Unit tests for SchedulingService.

Tests cover job creation and status transitions.
"""

from __future__ import annotations

import uuid

import pytest
from django.utils import timezone

from apps.scheduling.models import JobStatus
from apps.scheduling.services import SchedulingService, SchedulingServiceError


@pytest.mark.django_db
class TestSchedulingServiceCreateJob:
    """Tests for SchedulingService.create_job."""

    def test_creates_pending_job(self) -> None:
        """Verify job is created in PENDING status."""
        job = SchedulingService.create_job(
            name="Test Job",
            task_name="apps.test.task",
        )

        assert job.name == "Test Job"
        assert job.status == JobStatus.PENDING
        assert job.scheduled_for is not None

    def test_create_with_explicit_scheduled_for(self) -> None:
        """Verify job uses provided scheduled_for."""
        scheduled_time = timezone.now()
        job = SchedulingService.create_job(
            name="Test Job",
            task_name="apps.test.task",
            scheduled_for=scheduled_time,
        )

        assert job.scheduled_for == scheduled_time


@pytest.mark.django_db
class TestSchedulingServiceStatusTransitions:
    """Tests for SchedulingService status transition methods."""

    def test_mark_running(self) -> None:
        """Verify mark_running sets status and started_at."""
        job = SchedulingService.create_job(name="Test", task_name="apps.test.task")

        updated = SchedulingService.mark_running(job.id)

        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None

    def test_mark_completed(self) -> None:
        """Verify mark_completed sets status, finished_at, and result."""
        job = SchedulingService.create_job(name="Test", task_name="apps.test.task")

        updated = SchedulingService.mark_completed(job.id, result={"key": "value"})

        assert updated.status == JobStatus.COMPLETED
        assert updated.finished_at is not None
        assert updated.result == {"key": "value"}

    def test_mark_failed(self) -> None:
        """Verify mark_failed sets status, finished_at, and error."""
        job = SchedulingService.create_job(name="Test", task_name="apps.test.task")

        updated = SchedulingService.mark_failed(job.id, error="Something went wrong")

        assert updated.status == JobStatus.FAILED
        assert updated.finished_at is not None
        assert updated.error == "Something went wrong"

    def test_mark_skipped(self) -> None:
        """Verify mark_skipped sets status and reason."""
        job = SchedulingService.create_job(name="Test", task_name="apps.test.task")

        updated = SchedulingService.mark_skipped(job.id, reason="Not applicable")

        assert updated.status == JobStatus.SKIPPED
        assert updated.finished_at is not None

    def test_mark_running_nonexistent_raises_error(self) -> None:
        """Verify mark_running on nonexistent job raises error."""
        with pytest.raises(SchedulingServiceError):
            SchedulingService.mark_running(uuid.uuid4())

    def test_mark_completed_nonexistent_raises_error(self) -> None:
        """Verify mark_completed on nonexistent job raises error."""
        with pytest.raises(SchedulingServiceError):
            SchedulingService.mark_completed(uuid.uuid4())
