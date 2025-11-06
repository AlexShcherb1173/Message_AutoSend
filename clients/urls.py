from django.urls import path
from . import views

#: Пространство имён приложения для маршрутов клиентов.
#: Используется в шаблонах и вызовах reverse() как префикс "clients".
app_name = "clients"

#: Список URL-маршрутов приложения “clients”.
#:
#: Определяет навигацию для CRUD-действий над получателями рассылок (Recipient).
#: Каждый маршрут связан с конкретным классом представления, обрабатывающим соответствующее действие.
#:
#: ┌────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
#: │           URL              │          Представление       │             Имя              │
#: ├────────────────────────────┼──────────────────────────────┼──────────────────────────────┤
#: │ /clients/                  │ RecipientListView            │ clients:recipient_list       │
#: │ /clients/<id>/             │ RecipientDetailView          │ clients:recipient_detail     │
#: │ /clients/create/           │ RecipientCreateView          │ clients:recipient_create     │
#: │ /clients/<id>/edit/        │ RecipientUpdateView          │ clients:recipient_edit       │
#: │ /clients/<id>/delete/      │ RecipientDeleteView          │ clients:recipient_delete     │
#: └────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
urlpatterns = [
    path(
        "",
        views.RecipientListView.as_view(),
        name="recipient_list",
    ),
    path(
        "<int:pk>/",
        views.RecipientDetailView.as_view(),
        name="recipient_detail",
    ),
    path(
        "create/",
        views.RecipientCreateView.as_view(),
        name="recipient_create",
    ),
    path(
        "<int:pk>/edit/",
        views.RecipientUpdateView.as_view(),
        name="recipient_edit",
    ),
    path(
        "<int:pk>/delete/",
        views.RecipientDeleteView.as_view(),
        name="recipient_delete",
    ),
]