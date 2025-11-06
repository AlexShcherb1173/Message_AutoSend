from django.contrib import admin
from .models import Mailing, MailingStatus, MailingLog, MailingAttempt


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели Mailing (рассылка).
    Группирует поля по смысловым разделам через fieldsets:
      • «Параметры времени» — настройки окна рассылки.
      • «Содержимое» — что и кому отправляем.
      • «Статус» — текущее состояние и последняя отправка.
      • «Служебное» — системные метки (read-only).
    Также предоставляет действие «Пересчитать статус» для ручной синхронизации."""

    list_display = ("id", "status", "start_at", "end_at", "message", "created_at")
    list_filter = ("status", "start_at", "end_at", "created_at")
    search_fields = ("id", "message__title")  # подправь поле заголовка у Message при необходимости
    filter_horizontal = ("recipients",)
    readonly_fields = ("created_at", "updated_at", "last_sent_at")

    # Удобства навигации
    date_hierarchy = "created_at"
    save_on_top = True

    # Красиво структурируем форму редактирования
    fieldsets = (
        (
            "Параметры времени",
            {
                "fields": ("start_at", "end_at"),
            },
        ),
        (
            "Содержимое",
            {
                "fields": ("message", "recipients"),
            },
        ),
        (
            "Статус",
            {
                "fields": ("status", "last_sent_at"),
                "classes": ("collapse",),  # сворачиваемый блок
                "description": "Текущий статус пересчитывается автоматически по времени и факту отправок.",
            },
        ),
        (
            "Служебное",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
                "description": "Системные метки. Только для чтения.",
            },
        ),
    )

    actions = ["recompute_status"]

    @admin.action(description="Пересчитать статус у выбранных рассылок")
    def recompute_status(self, request, queryset):
        """Пересчитывает и сохраняет поле status для каждой выбранной рассылки.
        Args:
            request (HttpRequest): Объект запроса админки.
            queryset (QuerySet[Mailing]): Выбранные объекты рассылок."""
        for mailing in queryset:
            mailing.refresh_status(save=True)


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели MailingLog (лог событий рассылки)."""

    list_display = ("id", "mailing", "recipient", "status", "created_at", "triggered_by")
    list_filter = ("status", "created_at")
    search_fields = ("recipient", "detail", "triggered_by")


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели MailingAttempt (попытка рассылки)."""

    list_display = ("id", "mailing", "status", "attempted_at", "short_response")
    list_filter = ("status", "attempted_at")
    search_fields = ("server_response",)
    autocomplete_fields = ("mailing",)

    @admin.display(description="Ответ")
    def short_response(self, obj):
        """Возвращает сокращённый текст ответа сервера для отображения в списке.
        Args:
            obj (MailingAttempt): Текущий объект попытки.
        Returns:
            str: Усечённая строка (до 80 символов)."""
        txt = obj.server_response or ""
        return txt if len(txt) <= 80 else txt[:77] + "..."