from __future__ import annotations

import csv
from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpResponse
from django.utils.encoding import smart_str

User = get_user_model()


# ---------------------------- Admin actions ----------------------------------


@admin.action(description="Активировать выбранных пользователей")
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"Активировано: {updated}", level=messages.SUCCESS)


@admin.action(description="Деактивировать выбранных пользователей")
def deactivate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request, f"Деактивировано: {updated}", level=messages.WARNING
    )


@admin.action(description="Назначить статус персонала (is_staff=True)")
def make_staff(modeladmin, request, queryset):
    updated = queryset.update(is_staff=True)
    modeladmin.message_user(
        request, f"Назначено staff: {updated}", level=messages.SUCCESS
    )


@admin.action(description="Снять статус персонала (is_staff=False)")
def remove_staff(modeladmin, request, queryset):
    updated = queryset.update(is_staff=False)
    modeladmin.message_user(request, f"Снят staff: {updated}", level=messages.INFO)


@admin.action(description="Отправить ссылки для сброса пароля")
def send_password_reset(modeladmin, request, queryset):
    """Шлёт письма для сброса пароля через стандартную PasswordResetForm.
    Требуется настроенный email backend и включённый django.contrib.sites.
    Письма уходят только для активных пользователей с email (стандартное поведение формы).
    """
    sent = 0
    for user in queryset.iterator():
        if not user.email:
            continue
        form = PasswordResetForm({"email": user.email})
        if form.is_valid():
            form.save(
                request=request,  # нужен для построения абсолютной ссылки
                use_https=request.is_secure(),
                email_template_name="registration/password_reset_email.txt",
                html_email_template_name="registration/password_reset_email.html",
                subject_template_name="registration/password_reset_subject.txt",
            )
            sent += 1

    modeladmin.message_user(
        request, f"Отправлено писем: {sent}", level=messages.SUCCESS
    )


@admin.action(description="Экспортировать пользователей в CSV")
def export_users_csv(modeladmin, request, queryset):
    """Выгрузка CSV с колонками: id, email, is_active, is_staff, date_joined."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'
    writer = csv.writer(response, lineterminator="\n")
    writer.writerow(["id", "email", "is_active", "is_staff", "date_joined"])
    for u in queryset.iterator():
        writer.writerow(
            [u.pk, smart_str(u.email or ""), u.is_active, u.is_staff, u.date_joined]
        )
    return response


# ----------------------- Admin forms (без username) --------------------------


class UserCreationAdminForm(forms.ModelForm):
    """Форма создания пользователя в админке без поля username.
    Делает валидацию совпадения паролей и устанавливает хэш пароля."""

    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            "email",
            "avatar",
            "phone",
            "country",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserChangeAdminForm(forms.ModelForm):
    """Форма изменения пользователя в админке без поля username.
    Пароль редактируется через отдельную админскую форму смены пароля."""

    class Meta:
        model = User
        fields = (
            "email",
            "avatar",
            "phone",
            "country",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


# ------------------------------- Admin class ---------------------------------


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Админка кастомного пользователя (аутентификация по email).
    Поле username не используется; список и формы адаптированы под email."""

    model = User
    form = UserChangeAdminForm
    add_form = UserCreationAdminForm

    list_display = ("email", "is_active", "is_staff", "date_joined", "last_login")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("email", "phone", "country")
    ordering = ("-date_joined",)
    list_per_page = 25
    actions = [
        activate_users,
        deactivate_users,
        make_staff,
        remove_staff,
        send_password_reset,
        export_users_csv,
    ]
    actions_on_top = True

    # Убираем стандартное поле 'username' из секций
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("avatar", "phone", "country")}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Служебное", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    readonly_fields = ("last_login", "date_joined")
