from django.db import models
from django.core.validators import validate_email


class Recipient(models.Model):
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

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"