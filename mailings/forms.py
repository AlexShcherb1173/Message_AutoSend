from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import Mailing


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования объектов модели Mailing.
    Используется в представлениях:
        - MailingCreateView
        - MailingUpdateView
    Предоставляет:
        • Удобные поля ввода для дат/времени (HTML5 datetime-local).
        • Контекстные подсказки (help_text) для каждого поля.
        • Дополнительную валидацию логики времени рассылки."""

    class Meta:
        """Метаданные формы MailingForm.
        Определяет:
            - Модель, на основе которой строится форма.
            - Набор редактируемых полей.
            - Вспомогательные тексты (help_text) и виджеты."""

        model = Mailing
        fields = ["start_at", "end_at", "message", "recipients"]
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
        help_texts = {
            "start_at": "Укажите дату и время, когда рассылка должна начаться.",
            "end_at": "Задайте дату и время окончания рассылки (должно быть позже начала).",
            "message": "Выберите сообщение, которое будет отправлено получателям.",
            "recipients": "Выберите одного или несколько получателей из списка.",
        }

    def clean(self) -> dict:
        """Выполняет дополнительную валидацию временных полей.
        Проверяет два условия:
            1. Поле `end_at` должно быть позже `start_at`.
            2. Рассылка не может завершаться в прошлом (`end_at` > now).
        При нарушении добавляет ошибки в соответствующие поля.
        Returns:
            dict: Очищенные и проверенные данные формы."""
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")

        # Проверка последовательности дат
        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "Окончание должно быть позже начала.")

        # Проверка, что окончание не в прошлом
        if end_at and end_at <= timezone.now():
            self.add_error(
                "end_at",
                "Окончание уже прошло — рассылка не может быть создана в прошлом.",
            )

        return cleaned
