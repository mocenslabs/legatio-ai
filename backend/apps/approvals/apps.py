"""Approvals app configuration."""

from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    """Configuration for the approvals app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.approvals'
    verbose_name = 'Approvals'
