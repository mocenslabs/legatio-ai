"""Celery tasks for the scheduling app.

This module defines system-level scheduled tasks such as checking for
expired agreements and cleaning up old job records.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_expired_agreements() -> dict[str, Any]:
    """Check for active agreements that have expired.

    Finds all active agreements whose expiration date has passed
    and marks them as terminated. Each termination is recorded as
    a ScheduledJob.

    Returns:
        A summary dict with the number of expired agreements processed.
    """
    from apps.agreements.models import Agreement, AgreementStatus
    from apps.scheduling.services import SchedulingService

    job = SchedulingService.create_job(
        name="Check expired agreements",
        task_name="apps.scheduling.tasks.check_expired_agreements",
    )

    try:
        SchedulingService.mark_running(job.id)

        now = timezone.now()
        expired = Agreement.objects.filter(
            status=AgreementStatus.ACTIVE,
            expiration_date__lte=now,
        )

        count = 0
        for agreement in expired:
            agreement.status = AgreementStatus.TERMINATED
            agreement.save(update_fields=["status", "updated_at"])
            count += 1
            logger.info("Agreement %s expired and terminated", agreement.id)

        SchedulingService.mark_completed(
            job.id,
            result={"expired_count": count},
        )

        logger.info("Expired agreements check completed: %d terminated", count)
        return {"expired_count": count}

    except Exception as e:
        SchedulingService.mark_failed(job.id, error=str(e))
        logger.exception("Expired agreements check failed: %s", str(e))
        return {"error": str(e)}


@shared_task
def cleanup_old_jobs(days: int = 90) -> dict[str, Any]:
    """Delete old completed/failed job records.

    Removes ScheduledJob records older than the specified number of
    days to keep the table manageable.

    Args:
        days: Number of days to retain records. Defaults to 90.

    Returns:
        A summary dict with the number of deleted records.
    """
    from apps.scheduling.models import JobStatus, ScheduledJob

    cutoff = timezone.now() - timedelta(days=days)

    deleted_count, _ = ScheduledJob.objects.filter(
        status__in=[JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.SKIPPED],
        created_at__lt=cutoff,
    ).delete()

    logger.info("Cleaned up %d old job records (older than %d days)", deleted_count, days)

    return {"deleted_count": deleted_count, "days": days}
