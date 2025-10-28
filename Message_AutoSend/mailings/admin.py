from django.contrib import admin
from .models import Mailing, MailingStatus, MailingLog, MailingAttempt


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "start_at", "end_at", "message", "created_at")
    list_filter = ("status", "start_at", "end_at", "created_at")
    search_fields = ("id", "message__title")  # подправь поле заголовка у Message
    filter_horizontal = ("recipients",)
    readonly_fields = ("created_at", "updated_at", "last_sent_at")

    actions = ["recompute_status"]

    @admin.action(description="Пересчитать статус у выбранных рассылок")
    def recompute_status(self, request, queryset):
        for mailing in queryset:
            mailing.refresh_status(save=True)

@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    list_display = ("id", "mailing", "recipient", "status", "created_at", "triggered_by")
    list_filter = ("status", "created_at")
    search_fields = ("recipient", "detail", "triggered_by")

@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "mailing", "status", "attempted_at", "short_response")
    list_filter = ("status", "attempted_at")
    search_fields = ("server_response",)
    autocomplete_fields = ("mailing",)

    @admin.display(description="Ответ")
    def short_response(self, obj):
        txt = obj.server_response or ""
        return txt if len(txt) <= 80 else txt[:77] + "..."
