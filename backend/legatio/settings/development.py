"""
Development settings for Legatio AI project.
"""

from legatio.settings.base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "backend"]

# Debug toolbar (optional, only if installed)
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1", "172.0.0.0/8", "192.168.0.0/16"]
except ImportError:
    pass

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Simpler password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# CORS: allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Deterministic Fernet key for local development and tests only.
# Never use this value in production.
# CI sometimes sets ENCRYPTION_KEY to a non-Fernet placeholder; replace if invalid.
_DEV_FERNET_KEY = "8Pxuyu443UVl4gerNpnL2kduLqKdZ9wTFb-_g7Nv1iA="


def _is_valid_fernet_key(value: object) -> bool:
    if not value or not isinstance(value, str):
        return False
    key = value.strip()
    if not key or key.startswith("__") or key == "change-me":
        return False
    try:
        from cryptography.fernet import Fernet

        Fernet(key.encode("utf-8"))
        return True
    except Exception:
        return False


if not _is_valid_fernet_key(globals().get("ENCRYPTION_KEY")):
    ENCRYPTION_KEY = _DEV_FERNET_KEY
