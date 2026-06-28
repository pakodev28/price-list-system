"""Base Django settings shared across environments."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    # local
    "apps.suppliers",
    "apps.catalog",
    "apps.pricelists",
    "apps.projects",
    "apps.matching",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@db:5432/price_list",
    ),
}

# Scope: no authentication (single workspace). Keep validators minimal.
AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = []

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.DefaultPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Price List & Estimate API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/1")
CELERY_TASK_TRACK_STARTED = True

# CORS — permissive in this single-workspace prototype.
CORS_ALLOW_ALL_ORIGINS = True

# Matching / LLM configuration
MATCHER_STRATEGY = env("MATCHER_STRATEGY", default="hybrid")
MATCH_THRESHOLD = env.float("MATCH_THRESHOLD", default=0.75)
MATCH_SHORTLIST_SIZE = env.int("MATCH_SHORTLIST_SIZE", default=8)
MATCH_CONCURRENCY = env.int("MATCH_CONCURRENCY", default=8)
MATCH_ACCEPT_THRESHOLD = env.float("MATCH_ACCEPT_THRESHOLD", default=0.78)
MATCH_FLOOR = env.float("MATCH_FLOOR", default=0.40)
MATCH_GROUP_TOP_N = env.int("MATCH_GROUP_TOP_N", default=2)
LLM_ENABLED = env.bool("LLM_ENABLED", default=False)
LLM_BASE_URL = env("LLM_BASE_URL", default="")
LLM_API_KEY = env("LLM_API_KEY", default="")
LLM_MODEL = env("LLM_MODEL", default="dashscope/qwen3.5-plus")
LLM_TIMEOUT = env.float("LLM_TIMEOUT", default=30.0)
LLM_MAX_TOKENS = env.int("LLM_MAX_TOKENS", default=4096)
