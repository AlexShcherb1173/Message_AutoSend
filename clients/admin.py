from django.contrib import admin
from .models import Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели Recipient (получатель рассылки).
    Позволяет быстро управлять контактами, искать по email/ФИО/комментарию и
    видеть служебные метки.
    Особенности:
      • Список: email, ФИО, дата создания.
      • Поиск по email, ФИО и комментариям.
      • Фильтры по дате создания.
      • Поля created_at/updated_at — только для чтения."""

    list_display = ("email", "full_name", "created_at")
    search_fields = ("email", "full_name", "comment")
    list_filter = ("created_at",)
    ordering = ("full_name", "email")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("email", "full_name", "comment"),
                "description": (
                    "Укажите email (будет нормализован к нижнему регистру), "
                    "полное имя и при необходимости комментарий."
                ),
            },
        ),
        (
            "Служебные данные",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
                "description": "Системные временные метки (только чтение).",
            },
        ),
    )