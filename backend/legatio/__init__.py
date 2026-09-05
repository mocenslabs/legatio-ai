"""Legatio project package.

This module ensures the Celery app is loaded when Django starts,
so that shared_task decorators use this app.
"""

from legatio.celery import app as celery_app

__all__ = ["celery_app"]
