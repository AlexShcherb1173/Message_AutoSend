from __future__ import annotations

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings"))

app = Celery("config")

# Берём настройки из Django settings, все CELERY_* ключи подтянутся автоматически
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автопоиск tasks.py по INSTALLED_APPS
app.autodiscover_tasks()