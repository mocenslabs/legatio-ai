"""Celery tasks for the agents app.

This module defines scheduled and asynchronous tasks for automation
processing. Implementation will be completed in Phase 9 Step 3.
"""

from __future__ import annotations

from celery import shared_task


@shared_task
def ping() -> str:
    """Simple health-check task to verify Celery is working.

    Returns:
        A confirmation string.
    """
    return "pong"
