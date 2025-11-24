from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import Mailing


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылок.
    Возможности:
    • Bootstrap-стилизация всех полей.
    • HTML5 datetime-local для выбора даты/времени.
    • Подсказки к полям.
    • Дополнительная валидация логики времени."""

    class Meta:
        model = Mailing
        fields = ["start_at", "end_at", "message", "recipients"]

        # HTML5 виджеты для дат
        widgets = {
            "start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

        # Подсказки
        help_texts = {
            "start_at": "Когда запускать рассылку.",
            "end_at": "Когда останавливать рассылку (строго позже начала).",
            "message": "Выберите сообщение для отправки.",
            "recipients": "Укажите получателей (одного или несколько).",
        }

    def __init__(self, *args, **kwargs):
        """Добавляем Bootstrap-классы ко всем полям,
        а также плейсхолдеры для дат."""
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            # Множественный выбор — свои классы
            if isinstance(widget, (forms.CheckboxSelectMultiple,)):
                widget.attrs.setdefault("class", "form-check-input")

            # Обычно: input/select/textarea
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()

        # Плейсхолдеры дат
        if "start_at" in self.fields:
            self.fields["start_at"].widget.attrs.setdefault(
                "placeholder", "Выберите дату и время начала"
            )
        if "end_at" in self.fields:
            self.fields["end_at"].widget.attrs.setdefault(
                "placeholder", "Выберите дату и время завершения"
            )

    def clean(self) -> dict:
        """Дополнительная валидация:
        1. end_at > start_at
        2. end_at > сейчас"""
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")

        # Проверка: окончание позже начала
        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "Окончание должно быть позже начала.")

        # Проверка: окончание не в прошлом
        if end_at and end_at <= timezone.now():
            self.add_error(
                "end_at",
                "Дата окончания уже в прошлом — рассылка не может завершаться задним числом.",
            )

        return cleaned
