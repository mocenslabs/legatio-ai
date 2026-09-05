"""Celery application configuration for Legatio project.

This module defines the Celery app used for asynchronous task processing
and scheduled jobs. Settings are loaded from Django settings using the
CELERY namespace.
"""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

app = Celery("legatio")

# Load settings from Django settings, using the CELERY namespace.
# This means all Celery config keys must be prefixed with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps.
# Each app can define tasks in a tasks.py module.
app.autodiscover_tasks()
