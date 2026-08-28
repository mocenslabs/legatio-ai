"""Agreements app configuration."""

from django.apps import AppConfig


class AgreementsConfig(AppConfig):
    """Configuration for the agreements app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agreements"
    verbose_name = "Agreements"
