from django.db import models
from django.core.validators import MinLengthValidator


class Recipient(models.Model):
    """Модель получателя рассылки.

    Представляет человека или организацию, которым отправляются сообщения.
    Содержит уникальный email, Ф. И. О. и необязательный комментарий.
    Используется для формирования списка адресатов при запуске рассылок.
    """

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

    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
        help_text="Дата и время создания записи.",
    )
    updated_at = models.DateTimeField(
        "Обновлено",
        auto_now=True,
        help_text="Дата и время последнего обновления записи.",
    )

    class Meta:
        """Метаданные модели Recipient."""
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ("full_name", "email")  # удобнее просматривать в алфавитном порядке
        indexes = [
            models.Index(fields=["email"], name="idx_recipient_email"),
            models.Index(fields=["full_name"], name="idx_recipient_fullname"),
            models.Index(fields=["-created_at"], name="idx_recipient_created_desc"),
        ]

    def clean(self):
        """Нормализация данных перед валидацией/сохранением."""
        if self.email:
            self.email = self.email.strip().lower()
        if self.full_name:
            self.full_name = self.full_name.strip()

    def __str__(self) -> str:
        """Строковое представление в формате: «Ф. И. О. <email>»."""
        name = (self.full_name or "").strip()
        return f"{name} <{self.email}>".strip() if name else self.email