from __future__ import annotations

"""
Админ-интерфейс для приложения «mailings».

Что умеет:
  • Управление статусом рассылок (Запустить/Завершить/Сбросить).
  • Ручной запуск отправки (реально) и DRY-RUN (без реальной почты).
  • Экспорт логов/попыток в CSV и их очистка.
  • Отображение базовой статистики (KPI) по рассылке в списке (with_stats()).
  • Инлайны логов и попыток прямо в карточке рассылки.

Замечания:
  • Для производительности в списке используем get_queryset().with_stats()
    — см. кастомный QuerySet в models.py.
  • Поле triggered_by — CharField (email инициатора), НЕ используем select_related.
"""

import csv
from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponse
from django.utils.encoding import smart_str

from .models import Mailing, MailingAttempt, MailingLog, MailingStatus
from .services import send_mailing, SendResult


# ===== ВСПОМОГАТЕЛЬНОЕ =====
def _send_queryset(request, queryset, *, dry_run: bool):
    """Запустить send_mailing по выбранным рассылкам, вернуть агрегаты."""
    count_mailings = total = sent = skipped = 0
    for mailing in queryset:
        result: SendResult = send_mailing(mailing, user=request.user, dry_run=dry_run)
        count_mailings += 1
        total += result.total
        sent += result.sent
        skipped += result.skipped
    return count_mailings, total, sent, skipped


# ===== ДЕЙСТВИЯ СО СТАТУСОМ =====
@admin.action(description="Запустить (статус «Запущена»)")
def start_mailings(modeladmin, request, queryset):
    updated = queryset.update(status=MailingStatus.RUNNING)
    modeladmin.message_user(request, f"Обновлён статус «Запущена»: {updated}", level=messages.SUCCESS)


@admin.action(description="Завершить (статус «Завершена»)")
def finish_mailings(modeladmin, request, queryset):
    updated = queryset.update(status=MailingStatus.FINISHED)
    modeladmin.message_user(request, f"Обновлён статус «Завершена»: {updated}", level=messages.INFO)


@admin.action(description="Сбросить (статус «Создана»)")
def reset_mailings_to_created(modeladmin, request, queryset):
    updated = queryset.update(status=MailingStatus.CREATED)
    modeladmin.message_user(request, f"Обновлён статус «Создана»: {updated}", level=messages.WARNING)


# ===== ОТПРАВКА СЕЙЧАС / DRY-RUN =====
@admin.action(description="▶ Отправить сейчас")
def send_now(modeladmin, request, queryset):
    def _do():
        n, total, sent, skipped = _send_queryset(request, queryset, dry_run=False)
        modeladmin.message_user(
            request,
            f"Отправка завершена • рассылок: {n}, всего адресатов: {total}, отправлено: {sent}, пропущено/ошибок: {skipped}",
            level=messages.SUCCESS,
        )
    transaction.on_commit(_do)


@admin.action(description="🧪 DRY-RUN (без реальной отправки)")
def send_dry_run(modeladmin, request, queryset):
    def _do():
        n, total, sent, skipped = _send_queryset(request, queryset, dry_run=True)
        modeladmin.message_user(
            request,
            f"DRY-RUN завершён • рассылок: {n}, всего адресатов: {total}, отправлено бы: {total}, реально: 0 (skipped={skipped})",
            level=messages.WARNING,
        )
    transaction.on_commit(_do)


# ===== ЭКСПОРТ / ОЧИСТКА =====
@admin.action(description="Экспортировать попытки в CSV")
def export_attempts_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="mailing_attempts.csv"'
    writer = csv.writer(response)
    writer.writerow(["mailing_id", "attempted_at", "status", "triggered_by", "server_response"])
    qs = MailingAttempt.objects.filter(mailing__in=queryset).select_related("mailing")
    for a in qs.iterator():
        writer.writerow([a.mailing_id, a.attempted_at, smart_str(a.status), smart_str(a.triggered_by or ""), smart_str(a.server_response or "")])
    return response


@admin.action(description="Экспортировать логи в CSV")
def export_logs_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="mailing_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(["mailing_id", "created_at", "recipient", "status", "triggered_by", "detail"])
    qs = MailingLog.objects.filter(mailing__in=queryset).select_related("mailing")
    for log in qs.iterator():
        writer.writerow([log.mailing_id, log.created_at, smart_str(log.recipient), smart_str(log.status), smart_str(log.triggered_by or ""), smart_str(log.detail or "")])
    return response


# ===== INLINE'ы =====
class MailingLogInline(admin.TabularInline):
    """Инлайн-таблица логов прямо в карточке рассылки."""
    model = MailingLog
    extra = 0
    fields = ("created_at", "recipient", "status", "triggered_by", "detail")
    readonly_fields = ("created_at",)
    show_change_link = True
    ordering = ("-created_at",)


class MailingAttemptInline(admin.TabularInline):
    """Инлайн-таблица попыток отправки."""
    model = MailingAttempt
    extra = 0
    fields = ("attempted_at", "status", "triggered_by", "server_response")
    readonly_fields = ("attempted_at",)
    show_change_link = True
    ordering = ("-attempted_at",)


# ===== РЕГИСТРАЦИЯ =====
@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """
    Админ для Mailing с учётом ролей:
    • Менеджер (perm 'mailings.view_all_mailings') видит всё, но менять/удалять чужое не может.
    • Обычный пользователь видит и редактирует только свои записи.
    • В списке показываем базовые KPI (аннотации from with_stats()).
    """
    list_display = (
        "id",
        "owner",
        "status",
        "start_at",
        "end_at",
        "message_subject",
        "recipients_count",
        # KPI:
        "kpi_sent",
        "kpi_failed",
        "kpi_attempt_ok",
        "kpi_attempt_fail",
        "created_at",
    )
    list_filter = ("status", "start_at", "end_at", "created_at", "owner")
    search_fields = ("id", "message__subject", "owner__email")
    filter_horizontal = ("recipients",)
    readonly_fields = ("created_at", "updated_at", "last_sent_at")
    date_hierarchy = "start_at"
    save_on_top = True
    list_select_related = ("message", "owner")
    list_per_page = 25

    inlines = [MailingLogInline, MailingAttemptInline]

    actions = [
        "recompute_status",
        start_mailings, finish_mailings, reset_mailings_to_created,
        send_now, send_dry_run,
        export_attempts_csv, export_logs_csv,
    ]

    fieldsets = (
        ("Владелец", {"fields": ("owner",)}),
        ("Параметры времени", {"fields": ("start_at", "end_at")}),
        ("Содержимое", {"fields": ("message", "recipients")}),
        ("Статус", {"fields": ("status", "last_sent_at"), "classes": ("collapse",)}),
        ("Служебное", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """
        Оптимизируем запрос:
          • подтягиваем Message/owner,
          • аннотируем KPI через кастомный QuerySet.with_stats().
          • фильтруем по владельцу, если нет прав смотреть все.
        """
        qs = super().get_queryset(request).select_related("message", "owner").prefetch_related("recipients").with_stats()
        u = request.user
        if u.is_superuser or u.has_perm("mailings.view_all_mailings"):
            return qs
        return qs.filter(owner=u)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        u = request.user
        return u.is_superuser or obj.owner_id == u.id  # менеджер не меняет чужое

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        u = request.user
        return u.is_superuser or obj.owner_id == u.id

    @admin.display(description="Тема сообщения")
    def message_subject(self, obj: Mailing) -> str:
        subj = (getattr(obj.message, "subject", "") or "").strip()
        return subj if len(subj) <= 60 else subj[:57] + "..."

    @admin.display(description="Получателей")
    def recipients_count(self, obj: Mailing) -> int:
        return obj.recipients.count()

    # KPI-колонки
    @admin.display(description="Отправлено")
    def kpi_sent(self, obj: Mailing) -> int:
        return obj.stat_sent_messages

    @admin.display(description="Ошибок")
    def kpi_failed(self, obj: Mailing) -> int:
        return obj.stat_failed_messages

    @admin.display(description="Попыток OK")
    def kpi_attempt_ok(self, obj: Mailing) -> int:
        return obj.stat_attempt_success

    @admin.display(description="Попыток FAIL")
    def kpi_attempt_fail(self, obj: Mailing) -> int:
        return obj.stat_attempt_fail

    @admin.action(description="Пересчитать статус у выбранных рассылок")
    def recompute_status(self, request, queryset):
        updated = 0
        for m in queryset:
            prev = m.status
            m.refresh_status(save=True)
            if m.status != prev:
                updated += 1
        self.message_user(request, f"Статус пересчитан. Изменено записей: {updated}.")


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    """Админка поминутной телеметрии отправок (по каждому адресату)."""
    list_display = ("id", "mailing", "recipient", "status", "created_at", "triggered_by")
    list_filter = ("status", "created_at")
    search_fields = ("recipient", "detail", "triggered_by")  # triggered_by — строка
    ordering = ("-created_at",)
    list_select_related = ("mailing",)  # НЕ добавляем triggered_by (CharField)
    list_per_page = 50


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админка результатов батч-попыток."""
    list_display = ("id", "mailing", "status", "attempted_at", "triggered_by", "short_response")
    list_filter = ("status", "attempted_at")
    search_fields = ("server_response", "triggered_by")
    autocomplete_fields = ("mailing",)
    ordering = ("-attempted_at",)
    list_select_related = ("mailing",)
    list_per_page = 50

    @admin.display(description="Ответ")
    def short_response(self, obj):
        txt = obj.server_response or ""
        return txt if len(txt) <= 80 else txt[:77] + "..."