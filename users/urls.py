from django.urls import path, include
from .views import (
    SignUpView, SignUpDoneView, activate,
    EmailLoginView, EmailLogoutView,
    ProfileView, ProfileUpdateView
)

app_name = "users"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("signup/done/", SignUpDoneView.as_view(), name="signup_done"),
    path("activate/<uidb64>/<token>/", activate, name="activate"),

    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", EmailLogoutView.as_view(), name="logout"),

    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),

    # стандартные урлы восстановления пароля
    path("", include("django.contrib.auth.urls")),
]