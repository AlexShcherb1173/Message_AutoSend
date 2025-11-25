from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, TemplateView, DetailView, UpdateView

from .forms import CustomUserCreationForm, EmailAuthenticationForm, CustomUserChangeForm
from .models import User
from .utils import build_activation_link

logger = logging.getLogger(__name__)
User = get_user_model()


class SignUpView(CreateView):
    """Регистрация с подтверждением e-mail (письмо с токеном)."""

    template_name = "users/signup.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("users:signup_done")

    def form_valid(self, form):
        # 1. сохраняем пользователя НОРМАЛЬНО, с паролем
        user: User = form.save(commit=False)
        user.is_active = False
        user.save()
        form.save_m2m()  # если будут M2M поля

        # 2. генерируем токен ПОСЛЕ того, как пароль сохранён
        activation_link = build_activation_link(self.request, user)

        # 3. рендер письма
        try:
            html = render_to_string(
                "users/email/activation.html",
                {"activation_link": activation_link, "user": user},
            )
        except Exception:
            html = None

        # 4. отправляем письмо
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
    Упрощённый вариант:
    - по ссылке декодируем uidb64;
    - если пользователь существует и ещё не активен — активируем и логиним;
    - токен пока НЕ проверяем (используется как "шум" в URL)."""

    success_url = reverse_lazy("index")
    failure_url = reverse_lazy("users:signup")

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            user = None

        if not user:
            messages.error(request, "Пользователь не найден.")
            return redirect("users:signup")

        # Если уже активирован — просто сообщаем и ведём на логин
        if user.is_active:
            messages.info(request, "Аккаунт уже активирован. Войдите на сайт.")
            return redirect("users:login")

        # Активируем пользователя
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)
        messages.success(request, "Учётная запись активирована. Добро пожаловать!")
        return redirect("index")