from django.urls import path
from . import views

app_name = "mailings"

urlpatterns = [
    path("", views.MailingListView.as_view(), name="list"),
    path("<int:pk>/", views.MailingDetailView.as_view(), name="detail"),
    path("create/", views.MailingCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.MailingUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.MailingDeleteView.as_view(), name="delete"),
    path("<int:pk>/send/", views.MailingSendView.as_view(), name="send"),
]