from django.db import models
from django.core.validators import validate_email


class Recipient(models.Model):
    """ Модель получателя рассылки.
    Представляет человека или организацию, которым отправляются сообщения.
    Содержит контактный адрес электронной почты, полное имя и необязательный комментарий.
    Используется для формирования списка адресатов при запуске рассылок."""

    email = models.EmailField(
        "Email",
        unique=True,
        help_text="Уникальный адрес получателя"
    )
    full_name = models.CharField(
        "Ф. И. О.",
        max_length=255
    )
    comment = models.TextField(
        "Комментарий",
        blank=True
    )

    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
        help_text="Дата и время создания записи"
    )
    updated_at = models.DateTimeField(
        "Обновлено",
        auto_now=True,
        help_text="Дата и время последнего обновления записи"
    )

    class Meta:
        """Метаданные модели Recipient."""
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Возвращает строковое представление получателя.
        Returns:
            str: Формат 'Ф. И. О. <email>'."""
        return f"{self.full_name} <{self.email}>"