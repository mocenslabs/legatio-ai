"""
Celery application configuration for Legatio AI.

This module sets up the Celery instance used for async task processing
(LLM calls, audit processing, notifications, etc.).

Reference: 02-ARCHITECTURE.md Section 5.1 (ADR-006)
"""

import os

from celery import Celery
from celery.app.task import Task

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

# Create the Celery app
app = Celery("legatio")

# Load configuration from Django settings, using the CELERY_ namespace
# This means all Celery config must be prefixed with CELERY_ in settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
# This will look for a tasks.py module in each app
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self: Task) -> None:
    """
    Debug task to verify Celery is working correctly.

    This task simply prints the request info. Useful for testing
    that the Celery worker is properly connected to the broker.
    """
    print(f"Request: {self.request!r}")
