"""Policies app configuration."""

from django.apps import AppConfig


class PoliciesConfig(AppConfig):
    """Configuration for the policies app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.policies'
    verbose_name = 'Policies'
