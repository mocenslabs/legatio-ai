"""ScheduledJob model definition.

This module defines the ScheduledJob model, which records executions of
scheduled tasks. Each entry represents a single run of a periodic or
scheduled task, capturing its status, timing, and result.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class JobStatus(models.TextChoices):
    """Status lifecycle of a scheduled job execution."""

    PENDING = "PENDING", _("Pending")
    RUNNING = "RUNNING", _("Running")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")
    SKIPPED = "SKIPPED", _("Skipped")


class ScheduledJob(models.Model):
    """A record of a scheduled task execution.

    Each entry captures a single run of a periodic or scheduled task,
    including its status, timing, and result. This provides a history
    of automated activity and enables debugging of failed runs.

    Attributes:
        id: UUID primary key.
        name: Human-readable name for the job.
        task_name: The Celery task name or job identifier.
        status: Current execution status.
        automation_rule: Optional link to the automation rule being executed.
        scheduled_for: When the job was scheduled to run.
        started_at: When the job actually started.
        finished_at: When the job finished.
        result: JSON result of the execution.
        error: Error message if the job failed.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Human-readable name for the job."),
    )
    task_name = models.CharField(
        max_length=255,
        verbose_name=_("Task Name"),
        help_text=_("The Celery task name or job identifier."),
    )
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
        verbose_name=_("Status"),
        help_text=_("Current execution status."),
    )
    automation_rule = models.ForeignKey(
        "agents.AutomationRule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_jobs",
        verbose_name=_("Automation Rule"),
        help_text=_("Optional link to the automation rule being executed."),
    )
    scheduled_for = models.DateTimeField(
        verbose_name=_("Scheduled For"),
        help_text=_("When the job was scheduled to run."),
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Started At"),
        help_text=_("When the job actually started."),
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Finished At"),
        help_text=_("When the job finished."),
    )
    result = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Result"),
        help_text=_("JSON result of the execution."),
    )
    error = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Error"),
        help_text=_("Error message if the job failed."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )

    class Meta:
        verbose_name = _("Scheduled Job")
        verbose_name_plural = _("Scheduled Jobs")
        ordering = ["-scheduled_for"]
        indexes = [
            models.Index(fields=["status", "scheduled_for"]),
            models.Index(fields=["task_name", "scheduled_for"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the scheduled job."""
        return f"{self.name} ({self.status})"

    @property
    def is_finished(self) -> bool:
        """Check if the job has finished.

        Returns:
            True if the job is COMPLETED, FAILED, or SKIPPED.
        """
        return bool(self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.SKIPPED))

    @property
    def succeeded(self) -> bool:
        """Check if the job succeeded.

        Returns:
            True if the job status is COMPLETED.
        """
        return bool(self.status == JobStatus.COMPLETED)

    @property
    def duration_seconds(self) -> float | None:
        """Calculate the duration of the job in seconds.

        Returns:
            Duration in seconds, or None if the job hasn't finished.
        """
        if self.started_at is None or self.finished_at is None:
            return None
        return float((self.finished_at - self.started_at).total_seconds())
