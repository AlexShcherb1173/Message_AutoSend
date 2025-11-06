from django.contrib import admin
from django.urls import path, include
from . import views

#: Пространство имён приложения для URL-маршрутов.
#: Используется в шаблонах и функциях reverse() как префикс (например, "messages_app:message_list").
app_name = "messages_app"

#: Список URL-маршрутов приложения “messages_app”.
#:
#: Определяет навигацию для CRUD-операций над сообщениями,
#: которые используются в рассылках (создание, просмотр, редактирование, удаление).
#:
#: ┌────────────────────────────┬──────────────────────────────┬───────────────────────────────┐
#: │           URL              │          Представление       │              Имя              │
#: ├────────────────────────────┼──────────────────────────────┼───────────────────────────────┤
#: │ /messages/                 │ MessageListView              │ messages_app:message_list     │
#: │ /messages/create/          │ MessageCreateView            │ messages_app:message_create   │
#: │ /messages/<id>/            │ MessageDetailView            │ messages_app:message_detail   │
#: │ /messages/<id>/edit/       │ MessageUpdateView            │ messages_app:message_update   │
#: │ /messages/<id>/delete/     │ MessageDeleteView            │ messages_app:message_delete   │
#: └────────────────────────────┴──────────────────────────────┴───────────────────────────────┘
urlpatterns = [
    path(
        "",
        views.MessageListView.as_view(),
        name="message_list",
    ),
    path(
        "create/",
        views.MessageCreateView.as_view(),
        name="message_create",
    ),
    path(
        "<int:pk>/",
        views.MessageDetailView.as_view(),
        name="message_detail",
    ),
    path(
        "<int:pk>/edit/",
        views.MessageUpdateView.as_view(),
        name="message_update",
    ),
    path(
        "<int:pk>/delete/",
        views.MessageDeleteView.as_view(),
        name="message_delete",
    ),
]


