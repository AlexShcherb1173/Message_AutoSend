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

