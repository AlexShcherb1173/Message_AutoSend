from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели Message.
    Управляет созданием и редактированием сообщений, которые затем
    используются в рассылках. Предоставляет удобный интерфейс для
    просмотра, поиска и фильтрации сообщений.
    Особенности:
        • Отображает тему и дату создания в списке.
        • Поддерживает поиск по теме и тексту письма.
        • Позволяет фильтровать по дате создания.
        • Разделяет форму редактирования на логические блоки:
          «Содержимое» и «Служебные данные».
        • Поля created_at и updated_at доступны только для чтения."""

    list_display = ("subject", "created_at")
    search_fields = ("subject", "body")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    # Упорядочиваем поля по логическим секциям для удобства в админке
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
                "classes": ("collapse",),  # делает блок сворачиваемым
                "description": "Системные временные метки. Доступны только для чтения.",
            },
        ),
    )