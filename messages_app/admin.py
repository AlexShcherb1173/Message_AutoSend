from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели Message.

    Даёт быстрый просмотр/поиск по темам и текстам писем, которые затем
    используются в рассылках.
    Особенности:
      • Список: тема, дата создания, дата изменения.
      • Поиск по теме и телу письма.
      • Фильтрация по дате создания.
      • Поля created_at/updated_at доступны только для чтения.
    """

    list_display = ("subject", "created_at", "updated_at")
    search_fields = ("subject", "body")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

    fieldsets = (
        (
            "Содержимое",
            {
                "fields": ("subject", "body"),
                "description": "Введите тему и основной текст письма для рассылки.",
            },
        ),
        (
            "Служебные данные",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
                "description": "Системные метки. Только для чтения.",
            },
        ),
    )
