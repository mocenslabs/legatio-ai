"""Celery application configuration for Legatio AI."""

import logging
import os
from typing import Any

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

app = Celery("legatio")

# Load task modules from all registered Django apps.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps.
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    # Expire stale approvals every 5 minutes
    "expire-stale-approvals": {
        "task": "approvals.expire_stale_approvals",
        "schedule": 300.0,  # 5 minutes in seconds
    },
    # Verify audit chain daily at 2:00 AM UTC
    "verify-audit-chain-daily": {
        "task": "audit.verify_chain_daily",
        "schedule": crontab(hour=2, minute=0),
    },
    # Future: expire stale negotiations every 10 minutes
    # "expire-stale-negotiations": {
    #     "task": "negotiations.expire_stale_negotiations",
    #     "schedule": 600.0,  # 10 minutes
    # },
}

# Use Django's timezone
app.conf.timezone = "UTC"

logger = logging.getLogger("legatio.celery")


@app.task(bind=True, ignore_result=True)
def debug_task(self: Any) -> None:
    """Debug task to verify Celery is working."""
    logger.debug("Request: %r", self.request)
