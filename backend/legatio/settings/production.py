"""
Production settings for Legatio AI.

Used on Northflank (or similar) with Neon PostgreSQL and Redis addon.
Behind a TLS-terminating proxy: trust X-Forwarded-Proto / Host.
"""

from __future__ import annotations

import os
from typing import Any

from legatio.settings.base import *  # noqa: F401, F403
from legatio.settings.base import LOGGING

DEBUG = False

# ---------------------------------------------------------------------------
# Mandatory secrets — fail fast if still using development placeholders
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
        "ENCRYPTION_KEY must be a valid Fernet key in production. "
        'Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )

_secret = os.environ.get("DJANGO_SECRET_KEY", "")
if not _secret or _secret.startswith("__") or _secret == "change-me":
    raise ValueError("DJANGO_SECRET_KEY must be set to a strong random value in production.")

# ---------------------------------------------------------------------------
# TLS / reverse proxy (Northflank, Cloudflare, etc.)
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() in (
    "true",
    "1",
    "yes",
)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Neon requires SSL
if os.environ.get("POSTGRES_SSLMODE"):
    DATABASES["default"]["OPTIONS"]["sslmode"] = os.environ["POSTGRES_SSLMODE"]  # noqa: F405
else:
    DATABASES["default"]["OPTIONS"]["sslmode"] = "require"  # noqa: F405

# Logging
_log_config: dict[str, Any] = LOGGING
_log_config["root"]["level"] = os.environ.get("LOG_LEVEL", "INFO")
LOGGING = _log_config
