from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "created_at")
    search_fields = ("subject", "body")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
