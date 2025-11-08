from __future__ import annotations

from django.conf import settings
from django.db import models
from django.core.validators import MinLengthValidator


class Recipient(models.Model):
    """
    Получатель рассылки (клиент).
    Поле owner — владелец клиента; ограничения по владельцу.

    Храним:
      • email (уникальный),
      • полное имя (full_name),
      • комментарий (comment).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recipients",
        verbose_name="Владелец",
        help_text="Пользователь-владелец карточки клиента.",
    )

    email = models.EmailField(
        "Email",
        unique=True,
        help_text="Уникальный адрес получателя (будет приведён к нижнему регистру).",
    )
    full_name = models.CharField(
        "Ф. И. О.",
        max_length=255,
        validators=[MinLengthValidator(2, message="Минимум 2 символа.")],
        help_text="Полное имя получателя.",
    )
    comment = models.TextField(
        "Комментарий",
        blank=True,
        help_text="Дополнительная информация о получателе (необязательно).",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True, help_text="Дата и время создания записи.")
    updated_at = models.DateTimeField("Обновлено", auto_now=True, help_text="Дата и время последнего обновления записи.")

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ("full_name", "email")
        indexes = [
            models.Index(fields=["owner"], name="idx_recipient_owner"),
            models.Index(fields=["email"], name="idx_recipient_email"),
            models.Index(fields=["full_name"], name="idx_recipient_fullname"),
            models.Index(fields=["-created_at"], name="idx_recipient_created_desc"),
        ]
        permissions = (
            ("view_all_recipients", "Может просматривать всех получателей"),
        )

    def clean(self):
        """Нормализация данных перед валидацией/сохранением."""
        if self.email:
            self.email = self.email.strip().lower()
        if self.full_name:
            self.full_name = self.full_name.strip()

    def __str__(self) -> str:
        name = (self.full_name or "").strip()
        return f"{name} <{self.email}>".strip() if name else self.email