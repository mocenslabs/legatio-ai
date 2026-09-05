"""Celery tasks for the agents app.

This module defines scheduled and asynchronous tasks for automation
processing. These tasks are discovered automatically by Celery via
autodiscover_tasks.
"""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from apps.agents.models import TriggerType
from apps.agents.services import AutomationService
from apps.scheduling.services import SchedulingService

logger = logging.getLogger(__name__)


@shared_task
def ping() -> str:
    """Simple health-check task to verify Celery is working.

    Returns:
        A confirmation string.
    """
    return "pong"


@shared_task
def process_scheduled_rules() -> dict[str, Any]:
    """Process all active ON_SCHEDULE automation rules.

    This task is run periodically by Celery Beat. It finds all active
    rules with ON_SCHEDULE trigger and executes them, recording each
    execution as a ScheduledJob.

    Returns:
        A summary dict with executed and failed counts.
    """
    from apps.agents.models import AutomationRule

    rules = AutomationRule.objects.filter(
        trigger_type=TriggerType.ON_SCHEDULE,
        is_active=True,
        agent__is_active=True,
    ).order_by("priority", "-created_at")

    executed_count = 0
    failed_count = 0

    for rule in rules:
        job = SchedulingService.create_job(
            name=f"Scheduled: {rule.name}",
            task_name="apps.agents.tasks.process_scheduled_rules",
            automation_rule_id=rule.id,
        )

        try:
            SchedulingService.mark_running(job.id)

            result = AutomationService.execute_rule(
                rule_id=rule.id,
                context={},
            )

            SchedulingService.mark_completed(
                job.id,
                result={"executed": result, "rule_id": str(rule.id)},
            )
            executed_count += 1

        except Exception as e:
            SchedulingService.mark_failed(job.id, error=str(e))
            failed_count += 1
            logger.exception("Scheduled rule %s failed: %s", rule.id, str(e))

    logger.info(
        "Scheduled rules processed: %d executed, %d failed",
        executed_count,
        failed_count,
    )

    return {
        "executed": executed_count,
        "failed": failed_count,
        "total": executed_count + failed_count,
    }
