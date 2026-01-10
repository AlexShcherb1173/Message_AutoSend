from django.urls import include, path, re_path

from .views import (ActivateView, EmailLoginView, EmailLogoutView,
                    ProfileUpdateView, ProfileView, SignUpDoneView, SignUpView)

app_name = "users"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("signup/done/", SignUpDoneView.as_view(), name="signup_done"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", EmailLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path("", include("django.contrib.auth.urls")),
    re_path(
        r"^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$",
        ActivateView.as_view(),
        name="activate",
    ),
]
