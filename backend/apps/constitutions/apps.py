"""Constitutions app configuration."""

from django.apps import AppConfig


class ConstitutionsConfig(AppConfig):
    """Configuration for the constitutions app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.constitutions'
    verbose_name = 'Constitutions'
