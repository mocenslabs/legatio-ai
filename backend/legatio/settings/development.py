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
