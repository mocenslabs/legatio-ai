"""Throttles for the accounts app."""

from core.throttles import AuthAnonRateThrottle, SensitiveActionThrottle

__all__ = ["AuthAnonRateThrottle", "SensitiveActionThrottle"]
