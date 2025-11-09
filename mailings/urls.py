from django.urls import path
from . import views
from .views import MailingUserReportView

app_name = "mailings"

urlpatterns = [
    path("", views.MailingListView.as_view(), name="list"),
    path("<int:pk>/", views.MailingDetailView.as_view(), name="detail"),
    path("create/", views.MailingCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.MailingUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.MailingDeleteView.as_view(), name="delete"),
    path("<int:pk>/send/", views.MailingSendView.as_view(), name="send"),
    # отчёты
    path("stats/", views.MailingStatsView.as_view(), name="stats"),
    # менеджерская операция: отключить рассылку
    path("<int:pk>/disable/", views.MailingDisableView.as_view(), name="disable"),
    path("reports/", MailingUserReportView.as_view(), name="user_reports"),
]