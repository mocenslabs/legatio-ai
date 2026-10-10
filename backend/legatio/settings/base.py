"""
Base Django settings for Legatio AI project.
Common settings shared across all environments.
"""

import os
from pathlib import Path

# Agreement signing key (HMAC-SHA256)
SERVER_SIGNING_KEY = os.environ.get(
    "SERVER_SIGNING_KEY",
    "dev-only-signing-key-change-in-production",
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
DJANGO_APPS = [
    "daphne",  # Must be before django.contrib.staticfiles for ASGI
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "channels",
]

LOCAL_APPS = [
    "core",
    "apps.accounts",
    "apps.agents",
    "apps.constitutions",
    "apps.negotiations",
    "apps.proposals",
    "apps.approvals",
    "apps.agreements",
    "apps.audit",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "legatio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "legatio.wsgi.application"
ASGI_APPLICATION = "legatio.asgi.application"

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "legatio"),
        "USER": os.environ.get("POSTGRES_USER", "legatio"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "OPTIONS": {
            "sslmode": os.environ.get("POSTGRES_SSLMODE", "disable"),
        },
    }
}

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = os.environ.get("DJANGO_LANGUAGE_CODE", "en")
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],  # Will be configured in DEL-013
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    "DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost"
).split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://localhost"
).split(",")

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://redis:6379/0")],
        },
    },
}

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False").lower() in (
    "true",
    "1",
)

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "legatio": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# JWT Configuration
# =============================================================================
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "15"))
JWT_REFRESH_TOKEN_LIFETIME_DAYS = int(os.environ.get("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
JWT_ISSUER = os.environ.get("JWT_ISSUER", "legatio")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "legatio-clients")

# TOTP Configuration
TOTP_ISSUER = os.environ.get("TOTP_ISSUER", "LegatioAI")
TOTP_DIGITS = int(os.environ.get("TOTP_DIGITS", "6"))
TOTP_INTERVAL = int(os.environ.get("TOTP_INTERVAL", "30"))

# Update REST_FRAMEWORK with authentication classes
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "core.authentication.JWTAuthenticationWith2FA",
]

# =============================================================================
# JWT Configuration
# =============================================================================
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "15"))
JWT_REFRESH_TOKEN_LIFETIME_DAYS = int(os.environ.get("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
JWT_ISSUER = os.environ.get("JWT_ISSUER", "legatio")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "legatio-clients")

# TOTP Configuration
TOTP_ISSUER = os.environ.get("TOTP_ISSUER", "LegatioAI")
TOTP_DIGITS = int(os.environ.get("TOTP_DIGITS", "6"))
TOTP_INTERVAL = int(os.environ.get("TOTP_INTERVAL", "30"))

# Update REST_FRAMEWORK with authentication classes
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "core.authentication.JWTAuthenticationWith2FA",
]

# =============================================================================
# Custom Middleware
# =============================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware
    "core.middleware.CorrelationIdMiddleware",
    "core.middleware.RequestTimingMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
]
