"""
settings.py — основные настройки проекта Message_AutoSend.
Содержит конфигурацию Django: базы данных, установленные приложения,
пути к шаблонам, статику, медиафайлы, локализацию и параметры безопасности.
⚠️ Внимание:
    Этот файл предназначен для локальной разработки (DEBUG=True).
    Перед деплоем на сервер:
        • установи DEBUG = False;
        • задай ALLOWED_HOSTS;
        • перенеси SECRET_KEY в .env;
        • настрой EMAIL_BACKEND и базу данных.
"""

from pathlib import Path

# === ОСНОВНЫЕ ПУТИ ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent  # корень проекта


# === БЕЗОПАСНОСТЬ =============================================================
SECRET_KEY = "django-insecure-(u*qr^las*2v-rm*x^^&8$e#!qj9f)8z#1+^ov$78v#g&gbb)o"
DEBUG = True
ALLOWED_HOSTS: list[str] = []


# === ПРИЛОЖЕНИЯ ===============================================================
INSTALLED_APPS = [
    # Системные приложения Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Пользовательские приложения проекта
    "clients",        # управление получателями
    "messages_app",   # шаблоны сообщений
    "mailings",       # рассылки и лог отправок
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


# === URL-КОНФИГУРАЦИЯ ==========================================================
ROOT_URLCONF = "config.urls"


# === ШАБЛОНЫ ==================================================================
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


# === WSGI-ПРИЛОЖЕНИЕ ==========================================================
WSGI_APPLICATION = "config.wsgi.application"


# === БАЗА ДАННЫХ ==============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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
LANGUAGE_CODE = "en-us"   # Можно заменить на 'ru'
TIME_ZONE = "UTC"         # Например: 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# === СТАТИКА И МЕДИА ==========================================================
# --- Статические файлы ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # куда collectstatic будет собирать файлы
STATICFILES_DIRS: list[Path] = []        # дополнительные каталоги с локальной статикой

# --- Медиафайлы (загрузки пользователей) ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"          # каталог для хранения загружаемых файлов


# === ПОЧТА ===================================================================
# Для рассылок и уведомлений
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@example.com"
# Для боевого режима:
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.yourprovider.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = "user@example.com"
# EMAIL_HOST_PASSWORD = "secure-password"


# === ПРОЧЕЕ ==================================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"