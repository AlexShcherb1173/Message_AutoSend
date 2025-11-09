"""
settings.py — конфигурация проекта Message_AutoSend.
Читает переменные из .env (python-dotenv). Готов к PostgreSQL и SMTP.

Перед продакшеном:
  • DEBUG=False
  • задайте SECRET_KEY и ALLOWED_HOSTS
  • заполните SMTP-параметры (или используйте почтовый сервис/песочницу)
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# === БАЗОВЫЕ ПУТИ ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# === .ENV ====================================================================
load_dotenv(BASE_DIR / ".env")

def env_clean(name: str, default: str = "") -> str:
    """Безопасно получить строку из .env с зачисткой странных пробелов/кавычек."""
    s = os.getenv(name, default)
    if s is None:
        return default
    return (
        s.replace("\u00A0", " ")   # NBSP
         .replace("\u200B", "")    # zero-width
         .strip()
         .strip('"')
         .strip("'")
    )

def env_bool(name: str, default: bool = False) -> bool:
    """Булево из .env: 1/true/yes/on => True"""
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

def env_int(name: str, default: int) -> int:
    try:
        return int(env_clean(name, str(default)))
    except (TypeError, ValueError):
        return default

# === ПОЛЬЗОВАТЕЛЬСКАЯ МОДЕЛЬ =================================================
AUTH_USER_MODEL = "users.User"

# === БЕЗОПАСНОСТЬ ============================================================
SECRET_KEY = env_clean("SECRET_KEY", "change-me-dev-secret")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = [h.strip() for h in env_clean("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

# === ПРИЛОЖЕНИЯ ===============================================================
INSTALLED_APPS = [
    # Системные
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_apscheduler",

    # Сторонние
    "widget_tweaks",  # pip install django-widget-tweaks

    # Свои
    "users",
    "clients",
    "messages_app",
    "mailings",
]

SITE_ID = 1

# === MIDDLEWARE ===============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# === URL / ШАБЛОНЫ / WSGI ====================================================
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# === БАЗА ДАННЫХ (PostgreSQL) ================================================
DB_NAME = env_clean("DB_NAME", "message_autosend")
DB_USER = env_clean("DB_USER", "postgres")
DB_PASSWORD = env_clean("DB_PASSWORD", "postgres")
DB_HOST = env_clean("DB_HOST", "127.0.0.1")
DB_PORT = env_int("DB_PORT", 5432)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

# === АУТЕНТИФИКАЦИЯ / ПАРОЛИ ==================================================
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === ЛОКАЛИЗАЦИЯ ==============================================================
LANGUAGE_CODE = env_clean("LANGUAGE_CODE", "ru")
TIME_ZONE = env_clean("TIME_ZONE", "Europe/Amsterdam")
USE_I18N = True
USE_TZ = True

# === СТАТИКА И МЕДИА ==========================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []  # например: [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# === ПОЧТА (SMTP) =============================================================
# По умолчанию в DEBUG используем filebased backend (письма уходят в папку sent_emails).
# Если нужно отправлять по-настоящему в DEBUG, установи FORCE_SMTP=1 в .env.
FORCE_SMTP = env_bool("FORCE_SMTP", False)

if DEBUG and not FORCE_SMTP:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "sent_emails"
    DEFAULT_FROM_EMAIL = env_clean("DEFAULT_FROM_EMAIL", "webmaster@localhost")
    SERVER_EMAIL = env_clean("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
else:
    EMAIL_BACKEND = env_clean("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    EMAIL_HOST = env_clean("SMTP_HOST", "smtp.gmail.com")
    EMAIL_PORT = env_int("SMTP_PORT", 587)
    EMAIL_HOST_USER = env_clean("SMTP_USER", "")
    EMAIL_HOST_PASSWORD = env_clean("SMTP_PASSWORD", "")
    EMAIL_USE_TLS = env_bool("SMTP_USE_TLS", True)
    EMAIL_USE_SSL = env_bool("SMTP_USE_SSL", False)

    # Не допускаем одновременного TLS и SSL
    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        raise RuntimeError("EMAIL_USE_TLS и EMAIL_USE_SSL не могут быть True одновременно.")

    DEFAULT_FROM_EMAIL = env_clean("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@example.com")
    SERVER_EMAIL = env_clean("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# === ЛОГИН/ЛОГАУТ РЕДИРЕКТЫ ===================================================
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

# === ПРОЧЕЕ ===================================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = os.getenv("REDIS_URL")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "socket_timeout": 2,
            "socket_connect_timeout": 2,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        },
        "KEY_PREFIX": "msend",
        "TIMEOUT": 60 * 15,  # дефолт 15 минут
    }
}

# Включим Conditional GET + ETag (для 304 Not Modified)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "common.middleware.RequestContextMiddleware",
    "common.middleware.CurrentRequestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
]

USE_ETAGS = True  # пусть Django проставляет ETag на полноценные ответы

MAILINGS_MIN_REPEAT_MINUTES = int(os.getenv("MAILINGS_MIN_REPEAT_MINUTES", "5"))

LOG_DIR = BASE_DIR / "logs"
(LOG_DIR / "app").mkdir(parents=True, exist_ok=True)
(LOG_DIR / "requests").mkdir(parents=True, exist_ok=True)
(LOG_DIR / "security").mkdir(parents=True, exist_ok=True)
(LOG_DIR / "scheduler").mkdir(parents=True, exist_ok=True)

# кто получает письма при ERROR
ADMINS = [("Errors", os.getenv("ADMIN_EMAIL", "errors@yourdomain.com"))]

# ── LOGGING ─────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "common.logging_filters.RequestContextFilter",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "formatters": {
        "verbose": {
            "format": (
                "%(asctime)s | %(levelname)s | %(name)s | pid=%(process)d | "
                "rid=%(request_id)s | user=%(user_email)s | %(message)s"
            )
        },
        "simple": {
            "format": "%(levelname)s %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "verbose",
        },
        "app_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app" / "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["request_context"],
            "formatter": "verbose",
        },
        "requests_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "requests" / "requests.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 7,
            "encoding": "utf-8",
            "filters": ["request_context"],
            "formatter": "verbose",
        },
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "security" / "security.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["request_context"],
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        # наши прикладные логеры
        "app": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "app.requests": {
            "handlers": ["console", "requests_file"],
            "level": "INFO",
            "propagate": False,
        },
        "app.security": {
            "handlers": ["console", "security_file", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },

        # каждый django-приложение может логировать под своим именем
        "mailings": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "messages_app": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "clients": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },

        # системные логеры Django
        "django.request": {
            "handlers": ["console", "mail_admins", "requests_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "security_file", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        # Включи при необходимости трассировку SQL:
        # "django.db.backends": {
        #     "handlers": ["console"],
        #     "level": "INFO",
        #     "propagate": False,
        # },
    },
}


