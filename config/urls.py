"""
urls.py — корневая маршрутизация проекта Message_AutoSend.

Подключает административный интерфейс и все основные приложения:
    • mailings — рассылки;
    • clients — получатели;
    • messages_app — шаблоны сообщений;
а также определяет главную страницу проекта.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from mailings.views import HomeView

#: Корневые маршруты проекта Message_AutoSend.
#:
#: ┌────────────────────────────┬──────────────────────────────────────┬─────────────────────────────┐
#: │            URL             │          Представление / include     │            Имя              │
#: ├────────────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
#: │ /admin/                    │ Django Admin                        │ —                           │
#: │ /mailings/                 │ include('mailings.urls')             │ mailings:*                  │
#: │ /clients/                  │ include('clients.urls')              │ clients:*                   │
#: │ /messages_app/             │ include('messages_app.urls')         │ messages_app:*              │
#: │ /                          │ HomeView (главная страница)          │ home                        │
#: └────────────────────────────┴──────────────────────────────────────┴─────────────────────────────┘
urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include(("users.urls", "users"), namespace="users")),
    path("mailings/", include("mailings.urls")),
    path("clients/", include("clients.urls")),
    path("messages_app/", include("messages_app.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
]

# === Раздача медиа и статики при DEBUG ========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)