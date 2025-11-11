from __future__ import annotations
from django.contrib import messages
from django.views import View
from django.contrib.auth import (
    get_user_model,
    login,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import CreateView, TemplateView, DetailView, UpdateView
from .utils import build_activation_link

from .forms import CustomUserCreationForm, EmailAuthenticationForm, CustomUserChangeForm
from .models import User
from .tokens import activation_token_generator


class SignUpView(CreateView):
    """Регистрация с подтверждением e-mail (письмо с токеном)."""

    template_name = "users/signup.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("users:signup_done")

    def form_valid(self, form):
        user: User = form.save(commit=False)
        user.is_active = False
        user.save()
        link = build_activation_link(self.request, user)
        user.email_user(
            subject="Подтверждение регистрации",
            message=f"Для активации перейдите по ссылке: {link}",
            html_message=f"<p>Для активации перейдите по ссылке: <a href='{link}'>{link}</a></p>",
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_token_generator.make_token(user)
        activation_link = self.request.build_absolute_uri(
            reverse("users:activate", kwargs={"uidb64": uid, "token": token})
        )

        html = render_to_string(
            "users/email/activation.html",
            {"activation_link": activation_link, "user": user},
        )
        user.email_user(
            subject="Подтверждение регистрации",
            message=f"Для активации перейдите по ссылке: {activation_link}",
            html_message=html,
        )
        messages.info(
            self.request, "Мы отправили письмо с подтверждением на ваш e-mail."
        )
        return super().form_valid(form)


class SignUpDoneView(TemplateView):
    template_name = "users/signup_done.html"


def activate(request, uidb64: str, token: str):
    """Активация по ссылке из письма."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and activation_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "Аккаунт активирован. Войдите на сайт.")
        return redirect("users:login")
    messages.error(request, "Ссылка активации недействительна или устарела.")
    return redirect("users:signup")


class EmailLoginView(LoginView):
    """Вход по email."""

    template_name = "users/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class EmailLogoutView(LogoutView):
    """Выход."""

    next_page = reverse_lazy("index")


class ProfileView(LoginRequiredMixin, DetailView):
    """Просмотр профиля текущего пользователя."""

    model = User
    template_name = "users/profile.html"

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.request.user.pk)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля текущего пользователя."""

    model = User
    form_class = CustomUserChangeForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.request.user.pk)

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлён.")
        return super().form_valid(form)


User = get_user_model()


class ActivateView(View):
    """Подтверждение e-mail: /users/activate/<uidb64>/<token>/
    Если токен валиден — активирует пользователя и логинит.
    Иначе показывает предупреждение и отправляет на /users/signup/"""

    success_url = reverse_lazy("index")  # куда вести после успеха
    failure_url = reverse_lazy("users:signup")

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            login(request, user)
            messages.success(request, "Учётная запись активирована. Добро пожаловать!")
            return redirect("index")
        else:
            messages.success(request, "Ссылка активации недействительна или устарела.")
            return redirect("users:signup")
