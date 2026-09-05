"""
Base Django settings for Legatio AI project.

Contains settings common to all environments.
"""

from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=lambda v: [s.strip() for s in v.split(",")]
)

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "channels",
    "allauth",
    "allauth.account",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.agents",
    "apps.constitutions",
    "apps.policies",
    "apps.negotiations",
    "apps.proposals",
    "apps.approvals",
    "apps.agreements",
    "apps.audit",
    "apps.notifications",
    "apps.scheduling",
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
    "allauth.account.middleware.AccountMiddleware",
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
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="legatio"),
        "USER": config("DB_USER", default="legatio"),
        "PASSWORD": config("DB_PASSWORD", default="legatio"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardCursorPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (
                    config("REDIS_HOST", default="localhost"),
                    config("REDIS_PORT", default=6379, cast=int),
                )
            ],
        },
    },
}

# Celery
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Redis
REDIS_HOST = config("REDIS_HOST", default="localhost")
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)

# Site configuration
SITE_ID = 1

# Allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True

# API Documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "Legatio AI API",
    "DESCRIPTION": "AI-powered governance platform with policy engine, proposals, and agreements.",
    "VERSION": "0.5.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "ProposalStatusEnum": "apps.proposals.models.proposal.ProposalStatus",
        "ApprovalStatusEnum": "apps.approvals.models.approval_request.ApprovalStatus",
        "NotificationStatusEnum": "apps.notifications.models.notification.NotificationStatus",
        "NotificationTypeEnum": "apps.notifications.models.notification.NotificationType",
        "AgreementStatusEnum": "apps.agreements.models.agreement.AgreementStatus",
        "AuditActionEnum": "apps.audit.models.audit_log.AuditAction",
        "RuleActionTypeEnum": "apps.policies.models.policy_rule.RuleActionType",
        "DecisionOutcomeEnum": "apps.policies.engine.types.DecisionOutcome",
        "RiskLevelEnum": "apps.policies.engine.types.RiskLevel",
        "CommentEntityTypeEnum": "apps.negotiations.models.comment.CommentEntityType",
        "NegotiationStatusEnum": "apps.negotiations.models.negotiation.NegotiationStatus",
        "OfferStatusEnum": "apps.negotiations.models.negotiation_offer.OfferStatus",
        "AgentActionTypeEnum": "apps.agents.models.automation_rule.ActionType",
    },
}
