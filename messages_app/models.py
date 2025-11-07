from django.db import models
from django.core.validators import MinLengthValidator


class Message(models.Model):
    """Модель сообщения, используемого в рассылках.

    Содержит тему (subject) и текст письма (body), которые используются
    при формировании контента рассылки. Каждое сообщение может быть
    связано с одной или несколькими рассылками.
    """

    subject = models.CharField(
        "Тема письма",
        max_length=255,
        validators=[MinLengthValidator(1, message="Тема не может быть пустой.")],
        help_text="Короткий заголовок сообщения (отображается в поле Subject).",
    )
    body = models.TextField(
        "Тело письма",
        help_text="Основное содержимое письма в свободной форме.",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        """Метаданные модели Message."""
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at"], name="idx_msg_created_desc"),
            models.Index(fields=["subject"], name="idx_msg_subject"),
        ]

    def __str__(self) -> str:
        """Возвращает короткое представление сообщения: тема (до 80 символов).

        Если тема пуста (необычно, но возможно при прямых операциях с БД),
        вернёт «(без темы)».
        """
        subj = (self.subject or "").strip()
        return (subj[:80] if subj else "(без темы)")