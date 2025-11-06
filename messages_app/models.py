from django.db import models


class Message(models.Model):
    subject = models.CharField("Тема письма", max_length=255)
    body = models.TextField("Тело письма")

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.subject[:80] or "(без темы)"
