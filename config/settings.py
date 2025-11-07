"""
settings.py — конфигурация проекта Message_AutoSend.
Читает переменные из .env (python-dotenv). Готово к PostgreSQL и SMTP.

Перед продакшеном:
  • DEBUG=False
  • задайте SECRET_KEY и ALLOWED_HOSTS
  • заполните SMTP-параметры
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# === БАЗОВЫЕ ПУТИ ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# === .ENV ====================================================================
load_dotenv(BASE_DIR / ".env")

def env_clean(name: str, default: str = "") -> str:
    s = os.getenv(name, default)
    if s is None:
        return default
    # убрать неразрывные/нулевые пробелы и лишние кавычки
    return (
        s.replace("\u00A0", " ")
         .replace("\u200B", "")
         .strip()
         .strip('"')
         .strip("'")
    )

def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

# === БЕЗОПАСНОСТЬ ============================================================
SECRET_KEY = env_clean("SECRET_KEY", "change-me-dev-secret")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = [h.strip() for h in env_clean("ALLOWED_HOSTS","").split(",") if h.strip()]

# === ПРИЛОЖЕНИЯ ===============================================================
INSTALLED_APPS = [
    # Системные
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Пользовательские
    "clients",
    "messages_app",
    "mailings",
    "widget_tweaks",
]

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
# DB_* берём из .env (см. ниже пример .env)
DB_NAME = env_clean("DB_NAME", "message_autosend")
DB_USER = env_clean("DB_USER", "postgres")
DB_PASSWORD = env_clean("DB_PASSWORD", "postgres")
DB_HOST = env_clean("DB_HOST", "localhost")
try:
    DB_PORT = int(env_clean("DB_PORT", "5432"))
except ValueError:
    DB_PORT = 5432

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

# === ВАЛИДАЦИЯ ПАРОЛЕЙ =======================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === ЛОКАЛИЗАЦИЯ ==============================================================
LANGUAGE_CODE = env_clean("LANGUAGE_CODE", "en-us")
TIME_ZONE = env_clean("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# === СТАТИКА И МЕДИА ==========================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS: list[Path] = []  # например: [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# === ПОЧТА (SMTP) =============================================================
# Стандартная SMTP-схема: укажи EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT и т.д.
EMAIL_BACKEND = env_clean("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env_clean("EMAIL_HOST", "smtp.example.com")
try:
    EMAIL_PORT = int(env_clean("EMAIL_PORT", "587"))
except ValueError:
    EMAIL_PORT = 587
EMAIL_HOST_USER = env_clean("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_clean("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.com")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)  # отправитель системных ошибок

# === ПРОЧЕЕ ==================================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"