from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import Mailing


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_at", "end_at", "message", "recipients"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "Окончание должно быть позже начала.")
        # (опционально) запрет на создание полностью прошедшей рассылки
        if end_at and end_at <= timezone.now():
            self.add_error("end_at", "Окончание уже прошло.")
        return cleaned