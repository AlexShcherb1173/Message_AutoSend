from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.RecipientListView.as_view(), name="recipient_list"),
    path("<int:pk>/", views.RecipientDetailView.as_view(), name="recipient_detail"),
    path("create/", views.RecipientCreateView.as_view(), name="recipient_create"),
    path("<int:pk>/edit/", views.RecipientUpdateView.as_view(), name="recipient_edit"),
    path("<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient_delete"),
]