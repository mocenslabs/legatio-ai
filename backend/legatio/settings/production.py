"""
Production settings for Legatio AI project.
"""

import os
from typing import Any

from legatio.settings.base import *  # noqa: F401, F403
from legatio.settings.base import LOGGING

DEBUG = False

# ---------------------------------------------------------------------------
# Mandatory secrets — fail fast if still using development defaults
# ---------------------------------------------------------------------------
_bad_signing = (
    not SERVER_SIGNING_KEY  # noqa: F405
    or SERVER_SIGNING_KEY.startswith("dev-only")  # noqa: F405
    or SERVER_SIGNING_KEY.startswith("__")  # noqa: F405
)
if _bad_signing:
    raise ValueError("SERVER_SIGNING_KEY must be set to a strong random value in production.")

_bad_encryption = (
    not ENCRYPTION_KEY  # noqa: F405
    or ENCRYPTION_KEY.startswith("__")  # noqa: F405
    or ENCRYPTION_KEY == "change-me"  # noqa: F405
)
if _bad_encryption:
    raise ValueError(
        "ENCRYPTION_KEY must be set to a Fernet key in production. "
        'Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )

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
