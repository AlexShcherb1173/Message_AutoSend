from __future__ import annotations

import csv
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.encoding import smart_str
from .models import Message


@admin.action(description="Дублировать выбранные сообщения")
def duplicate_messages(modeladmin, request, queryset):
    """Создаёт копию каждого сообщения.
    Тема дополнена суффиксом ' (копия)'.
    Создаём новые экземпляры через Message.objects.create(),
    чтобы не мутировать исходный объект и не полагаться на obj.pk = None."""
    created = 0
    for src in queryset.iterator():
        Message.objects.create(
            subject=f"{src.subject} (копия)",
            body=src.body,
        )
        created += 1

    modeladmin.message_user(
        request,
        f"Создано копий: {created}",
        level=messages.SUCCESS,
    )


@admin.action(description="Экспортировать выбранные сообщения в CSV")
def export_messages_csv(modeladmin, request, queryset):
    """Экспорт выбранных сообщений в CSV.
    Используем lineterminator='\\n' для корректной совместимости с Windows."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="messages.csv"'

    writer = csv.writer(response, lineterminator="\n")
    writer.writerow(["id", "subject", "created_at", "updated_at", "body"])

    for m in queryset.iterator():
        writer.writerow(
            [
                m.pk,
                smart_str(m.subject or ""),
                m.created_at,
                m.updated_at,
                smart_str(m.body or ""),
            ]
        )

    return response


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели Message.
    • Список: тема, дата создания/изменения
    • Поиск: по теме и телу письма
    • Фильтры: по дате создания
    • Экшены: дублирование, экспорт в CSV"""

    list_display = ("subject", "created_at", "updated_at")
    search_fields = ("subject", "body")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    date_hierarchy = "created_at"

    # Подключаем экшены
    actions = [duplicate_messages, export_messages_csv]
    actions_on_top = True

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
                "description": "Системные метки, доступны только для чтения.",
            },
        ),
    )
