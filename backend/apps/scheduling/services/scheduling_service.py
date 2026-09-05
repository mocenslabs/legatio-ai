"""Scheduling Service layer.

This module provides a service for managing scheduled job executions,
including creating job records, updating their status, and querying
execution history.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from django.utils import timezone

from apps.scheduling.models import JobStatus, ScheduledJob

logger = logging.getLogger(__name__)


class SchedulingServiceError(Exception):
    """Base exception for scheduling service errors."""


class SchedulingService:
    """Service layer for scheduled job operations.

    Manages the lifecycle of scheduled job records: creation, status
    updates, and querying.
    """

    @staticmethod
    def create_job(
        name: str,
        task_name: str,
        scheduled_for: Any | None = None,
        automation_rule_id: uuid.UUID | None = None,
    ) -> ScheduledJob:
        """Create a new scheduled job record.

        Args:
            name: Human-readable name for the job.
            task_name: The Celery task name or job identifier.
            scheduled_for: When the job is scheduled to run (defaults to now).
            automation_rule_id: Optional UUID of the related automation rule.

        Returns:
            The created ScheduledJob instance.
        """
        if scheduled_for is None:
            scheduled_for = timezone.now()

        job = ScheduledJob.objects.create(
            name=name,
            task_name=task_name,
            scheduled_for=scheduled_for,
            automation_rule_id=automation_rule_id,
            status=JobStatus.PENDING,
        )

        logger.info("Created scheduled job %s: %s", job.id, name)
        return job

    @staticmethod
    def mark_running(job_id: uuid.UUID) -> ScheduledJob:
        """Mark a job as running.

        Args:
            job_id: The UUID of the job.

        Returns:
            The updated ScheduledJob instance.

        Raises:
            SchedulingServiceError: If the job doesn't exist.
        """
        job = SchedulingService._get_job(job_id)
        job.status = JobStatus.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at", "updated_at"])

        logger.info("Job %s is now running", job_id)
        return job

    @staticmethod
    def mark_completed(
        job_id: uuid.UUID,
        result: dict[str, Any] | None = None,
    ) -> ScheduledJob:
        """Mark a job as completed.

        Args:
            job_id: The UUID of the job.
            result: Optional JSON result of the execution.

        Returns:
            The updated ScheduledJob instance.

        Raises:
            SchedulingServiceError: If the job doesn't exist.
        """
        job = SchedulingService._get_job(job_id)
        job.status = JobStatus.COMPLETED
        job.finished_at = timezone.now()
        job.result = result
        job.save(update_fields=["status", "finished_at", "result", "updated_at"])

        logger.info("Job %s completed", job_id)
        return job

    @staticmethod
    def mark_failed(
        job_id: uuid.UUID,
        error: str,
    ) -> ScheduledJob:
        """Mark a job as failed.

        Args:
            job_id: The UUID of the job.
            error: Error message describing the failure.

        Returns:
            The updated ScheduledJob instance.

        Raises:
            SchedulingServiceError: If the job doesn't exist.
        """
        job = SchedulingService._get_job(job_id)
        job.status = JobStatus.FAILED
        job.finished_at = timezone.now()
        job.error = error
        job.save(update_fields=["status", "finished_at", "error", "updated_at"])

        logger.error("Job %s failed: %s", job_id, error)
        return job

    @staticmethod
    def mark_skipped(
        job_id: uuid.UUID,
        reason: str = "",
    ) -> ScheduledJob:
        """Mark a job as skipped.

        Args:
            job_id: The UUID of the job.
            reason: Optional reason for skipping.

        Returns:
            The updated ScheduledJob instance.

        Raises:
            SchedulingServiceError: If the job doesn't exist.
        """
        job = SchedulingService._get_job(job_id)
        job.status = JobStatus.SKIPPED
        job.finished_at = timezone.now()
        job.error = reason
        job.save(update_fields=["status", "finished_at", "error", "updated_at"])

        logger.info("Job %s skipped: %s", job_id, reason)
        return job

    @staticmethod
    def _get_job(job_id: uuid.UUID) -> ScheduledJob:
        """Retrieve a scheduled job or raise an error.

        Args:
            job_id: The UUID of the job.

        Returns:
            The ScheduledJob instance.

        Raises:
            SchedulingServiceError: If the job doesn't exist.
        """
        try:
            return ScheduledJob.objects.get(id=job_id)
        except ScheduledJob.DoesNotExist as e:
            raise SchedulingServiceError(f"Job {job_id} not found") from e
