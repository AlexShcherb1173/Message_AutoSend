from django.contrib import admin
from .models import Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "created_at")
    search_fields = ("email", "full_name", "comment")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
