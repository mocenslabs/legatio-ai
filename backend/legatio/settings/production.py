"""Production settings for Legatio project.

This module inherits from base settings and overrides them with
production-specific configurations for security, performance, and
external services.
"""

from __future__ import annotations

import os

from legatio.settings.base import *  # noqa: F403

# ──────────────────────────────────────────────
# Security & Debug
# ──────────────────────────────────────────────
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production.")

# SECURITY WARNING: update this with your actual domain(s)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Security headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# ──────────────────────────────────────────────
# Database (PostgreSQL)
# Uses the same DB_* environment variables as the CI pipeline
# ──────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "legatio"),
        "USER": os.getenv("DB_USER", "legatio"),
        "PASSWORD": os.getenv("DB_PASSWORD", "legatio"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,  # Connection pooling
        "OPTIONS": {
            "sslmode": "require"
            if os.getenv("DATABASE_SSL_REQUIRE", "False").lower() == "true"
            else "prefer",
        },
    }
}

# ──────────────────────────────────────────────
# Caching & Redis
# ──────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", REDIS_URL),
    }
}

# Celery Broker & Backend
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", REDIS_URL))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

# ──────────────────────────────────────────────
# Static & Media Files
# ──────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / "staticfiles"  # type: ignore # noqa: F405
MEDIA_ROOT = BASE_DIR / "mediafiles"  # type: ignore # noqa: F405
MEDIA_URL = "/media/"

# Nota: Si decides instalar 'whitenoise' en el futuro para servir estáticos,
# agrégalo a INSTALLED_APPS en base.py y descomenta esto:
# STORAGES = {
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ──────────────────────────────────────────────
# Django REST Framework & Spectacular
# ──────────────────────────────────────────────
# Stricter throttling for production
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # type: ignore
    "burst": os.getenv("THROTTLE_BURST_RATE", "60/min"),
    "sustained": os.getenv("THROTTLE_SUSTAINED_RATE", "1000/day"),
    "anon_burst": os.getenv("THROTTLE_ANON_BURST_RATE", "10/min"),
}
