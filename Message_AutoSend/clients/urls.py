from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.RecipientListView.as_view(), name="recipient_list"),
    path("create/", views.RecipientCreateView.as_view(), name="recipient_create"),
    path("<int:pk>/", views.RecipientDetailView.as_view(), name="recipient_detail"),
    path("<int:pk>/edit/", views.RecipientUpdateView.as_view(), name="recipient_update"),
    path("<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient_delete"),
]
В Message_AutoSend/urls.py (или project/urls.py) подключаем:

python
Копировать код
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("clients/", include("clients.urls", namespace="clients")),
    path("", include("clients.urls", namespace="clients")),  # опционально — список на главной
]