"""
Production settings for Legatio AI project.
"""

import os
from typing import Any

from legatio.settings.base import *  # noqa: F401, F403
from legatio.settings.base import LOGGING

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() in ("true", "1")  # noqa: F405
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Logging - override root level for production
_log_config: dict[str, Any] = LOGGING
_log_config["root"]["level"] = "WARNING"
LOGGING = _log_config
