"""Agents app configuration."""

from django.apps import AppConfig


class AgentsConfig(AppConfig):
    """Configuration for the agents app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agents"
    verbose_name = "Agents"
