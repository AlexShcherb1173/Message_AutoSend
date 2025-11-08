from django.urls import path, re_path, include
from .views import (
    SignUpView, SignUpDoneView, activate,
    EmailLoginView, EmailLogoutView,
    ProfileView, ProfileUpdateView, ActivateView,
)

app_name = "users"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("signup/done/", SignUpDoneView.as_view(), name="signup_done"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", EmailLogoutView.as_view(), name="logout"),

    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),

    # 🔐 восстановление пароля (станут namespaced: users:password_reset, ...)
    path("", include("django.contrib.auth.urls")),

    # ✅ ВАЖНО: теперь этот маршрут внутри urlpatterns
    re_path(
        r"^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$",
        ActivateView.as_view(),
        name="activate",
    ),
]