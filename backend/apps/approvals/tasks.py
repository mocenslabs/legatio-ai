"""
Celery tasks for approval management.

Source: 04-BUSINESS-FLOW.md Section 9.4
"""

import logging

from apps.approvals.services import expire_stale_approvals
from celery import shared_task

logger = logging.getLogger("legatio.approvals.tasks")


@shared_task(name="approvals.expire_stale_approvals")  # type: ignore[misc]
def expire_stale_approvals_task() -> dict[str, int]:
    """
    Celery task to expire stale approval requests.

    Runs every 5 minutes via Celery Beat.

    Returns:
        Dictionary with the number of expired requests.
    """
    logger.info("Starting expire_stale_approvals task")
    expired_count = expire_stale_approvals()
    logger.info(f"Expired {expired_count} approval requests")
    return {"expired_count": expired_count}
