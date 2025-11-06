from django.urls import path
from . import views

#: Пространство имён приложения.
#: Используется для namespacing URL-имен в шаблонах и reverse() вызовах.
app_name = "mailings"

#: URL-маршруты приложения "mailings".
#:
#: Определяют навигацию по CRUD-действиям (создание, просмотр, редактирование,
#: удаление, запуск рассылки).
#:
#: ┌────────────────────────────┬──────────────────────────────┬──────────────────┐
#: │          URL               │          Представление       │       Имя        │
#: ├────────────────────────────┼──────────────────────────────┼──────────────────┤
#: │ /mailings/                 │ MailingListView              │ mailings:list    │
#: │ /mailings/<id>/            │ MailingDetailView            │ mailings:detail  │
#: │ /mailings/create/          │ MailingCreateView            │ mailings:create  │
#: │ /mailings/<id>/edit/       │ MailingUpdateView            │ mailings:edit    │
#: │ /mailings/<id>/delete/     │ MailingDeleteView            │ mailings:delete  │
#: │ /mailings/<id>/send/       │ MailingSendView (POST-only)  │ mailings:send    │
#: └────────────────────────────┴──────────────────────────────┴──────────────────┘
urlpatterns = [
    path(
        "",
        views.MailingListView.as_view(),
        name="list",
    ),
    path(
        "<int:pk>/",
        views.MailingDetailView.as_view(),
        name="detail",
    ),
    path(
        "create/",
        views.MailingCreateView.as_view(),
        name="create",
    ),
    path(
        "<int:pk>/edit/",
        views.MailingUpdateView.as_view(),
        name="edit",
    ),
    path(
        "<int:pk>/delete/",
        views.MailingDeleteView.as_view(),
        name="delete",
    ),
    path(
        "<int:pk>/send/",
        views.MailingSendView.as_view(),
        name="send",
    ),
]