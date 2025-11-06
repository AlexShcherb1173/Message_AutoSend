import os
import sys
from pathlib import Path

# гарантируем, что корень проекта в sys.path (папка с manage.py)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# УКАЖИ реальный модуль настроек!
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # или "Message_AutoSend.settings"

import django
django.setup()