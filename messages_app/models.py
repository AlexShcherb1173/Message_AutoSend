from __future__ import annotations

from django.conf import settings
from django.db import models
from django.core.validators import MinLengthValidator


class Message(models.Model):
    """
    Шаблон письма для рассылок.
    Поле owner — кто создал сообщение; ограничение доступа по владельцу.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="messages_owned",
        verbose_name="Владелец",
        help_text="Пользователь-владелец шаблона сообщения.",
    )

    subject = models.CharField(
        "Тема письма",
        max_length=255,
        validators=[MinLengthValidator(1, message="Тема не может быть пустой.")],
        help_text="Короткий заголовок сообщения (отображается в поле Subject).",
    )
    body = models.TextField(
        "Текст письма",
        help_text="Основное содержимое письма в свободной форме.",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["owner"], name="idx_message_owner"),
            models.Index(fields=["-created_at"], name="idx_msg_created_desc"),
            models.Index(fields=["subject"], name="idx_msg_subject"),
        ]
        permissions = (
            ("view_all_messages", "Может просматривать все сообщения"),
        )

    def __str__(self) -> str:
        subj = (self.subject or "").strip()
        return subj[:80] if subj else "(без темы)"