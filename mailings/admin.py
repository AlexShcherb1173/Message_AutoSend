from django.contrib import admin
from .models import Mailing, MailingStatus, MailingLog, MailingAttempt


class MailingLogInline(admin.TabularInline):
    """Инлайн-таблица логов для быстрой диагностики прямо в карточке рассылки."""
    model = MailingLog
    extra = 0
    fields = ("created_at", "recipient", "status", "triggered_by", "detail")
    readonly_fields = ("created_at",)
    show_change_link = True
    ordering = ("-created_at",)


class MailingAttemptInline(admin.TabularInline):
    """Инлайн-таблица агрегированных попыток отправки (батчи/джобы)."""
    model = MailingAttempt
    extra = 0
    fields = ("attempted_at", "status", "server_response")
    readonly_fields = ("attempted_at",)
    show_change_link = True
    ordering = ("-attempted_at",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели Mailing (рассылка).

    Группировка полей по блокам и удобные инструменты для операционного контроля.
    Особенности:
      • Список: статус, окно времени, тема сообщения, количество получателей.
      • Поиск по ID и теме сообщения.
      • Фильтры по статусу и датам.
      • Действие «Пересчитать статус».
      • Инлайны логов и попыток для быстрой диагностики.
    """

    list_display = (
        "id",
        "status",
        "start_at",
        "end_at",
        "message_subject",
        "recipients_count",
        "created_at",
    )
    list_filter = ("status", "start_at", "end_at", "created_at")
    # ВАЖНО: поле темы у Message — subject (не title)
    search_fields = ("id", "message__subject")
    filter_horizontal = ("recipients",)
    readonly_fields = ("created_at", "updated_at", "last_sent_at")
    date_hierarchy = "start_at"
    save_on_top = True
    list_select_related = ("message",)
    list_per_page = 25
    inlines = [MailingLogInline, MailingAttemptInline]
    actions = ["recompute_status"]

    fieldsets = (
        (
            "Параметры времени",
            {"fields": ("start_at", "end_at")},
        ),
        (
            "Содержимое",
            {"fields": ("message", "recipients")},
        ),
        (
            "Статус",
            {
                "fields": ("status", "last_sent_at"),
                "classes": ("collapse",),
                "description": "Статус пересчитывается автоматически по времени и факту отправок.",
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

    def get_queryset(self, request):
        """Оптимизируем запрос: подтягиваем Message и считаем получателей."""
        qs = super().get_queryset(request)
        return qs.select_related("message").prefetch_related("recipients")

    @admin.display(description="Тема сообщения")
    def message_subject(self, obj: Mailing) -> str:
        """Короткая тема связанного сообщения (для списка)."""
        subj = (obj.message.subject or "").strip()
        return subj if len(subj) <= 60 else subj[:57] + "..."

    @admin.display(description="Получателей")
    def recipients_count(self, obj: Mailing) -> int:
        """Количество получателей у рассылки (быстрый просмотр в списке)."""
        return obj.recipients.count()

    @admin.action(description="Пересчитать статус у выбранных рассылок")
    def recompute_status(self, request, queryset):
        """Пересчитывает и сохраняет поле status для выбранных рассылок."""
        updated = 0
        for mailing in queryset:
            prev = mailing.status
            mailing.refresh_status(save=True)
            if mailing.status != prev:
                updated += 1
        self.message_user(
            request,
            f"Статус пересчитан. Изменено записей: {updated}."
        )


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели MailingLog (поминутная телеметрия отправок)."""

    list_display = ("id", "mailing", "recipient", "status", "created_at", "triggered_by")
    list_filter = ("status", "created_at")
    search_fields = ("recipient", "detail", "triggered_by")
    ordering = ("-created_at",)
    list_select_related = ("mailing",)
    list_per_page = 50


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админ-интерфейс для модели MailingAttempt (результаты батч-попыток)."""

    list_display = ("id", "mailing", "status", "attempted_at", "short_response")
    list_filter = ("status", "attempted_at")
    search_fields = ("server_response",)
    autocomplete_fields = ("mailing",)
    ordering = ("-attempted_at",)
    list_select_related = ("mailing",)
    list_per_page = 50

    @admin.display(description="Ответ")
    def short_response(self, obj):
        """Усечённый текст ответа сервера для списка (до 80 символов)."""
        txt = obj.server_response or ""
        return txt if len(txt) <= 80 else txt[:77] + "..."