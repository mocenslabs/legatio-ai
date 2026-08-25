"""Negotiations app configuration."""

from django.apps import AppConfig


class NegotiationsConfig(AppConfig):
    """Configuration for the negotiations app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.negotiations'
    verbose_name = 'Negotiations'
