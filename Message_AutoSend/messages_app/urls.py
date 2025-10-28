from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "messages_app"

urlpatterns = [
    path("", views.MessageListView.as_view(), name="message_list"),
    path("create/", views.MessageCreateView.as_view(), name="message_create"),
    path("<int:pk>/", views.MessageDetailView.as_view(), name="message_detail"),
    path("<int:pk>/edit/", views.MessageUpdateView.as_view(), name="message_update"),
    path("<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete"),
    path("admin/", admin.site.urls),
    path("clients/", include("clients.urls", namespace="clients")),
    path("messages/", include("messages_app.urls", namespace="messages_app")),
]


