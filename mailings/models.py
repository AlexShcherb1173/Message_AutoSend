from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class MailingStatus(models.TextChoices):
    CREATED = "Создана", "Создана"
    RUNNING = "Запущена", "Запущена"
    FINISHED = "Завершена", "Завершена"


class Mailing(models.Model):
    """
    Рассылка:
    - start_at: дата и время первой отправки
    - end_at: дата и время окончания
    - status: Создана / Запущена / Завершена
    - message: FK на messages_app.Message
    - recipients: M2M на clients.Recipient
    - last_sent_at: служебно — чтобы понимать, отправлялась ли уже
    """

    start_at = models.DateTimeField("Дата/время первой отправки")
    end_at = models.DateTimeField("Дата/время окончания")
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=MailingStatus.choices,
        default=MailingStatus.CREATED,
    )
    message = models.ForeignKey(
        "messages_app.Message",
        on_delete=models.PROTECT,
        verbose_name="Сообщение",
        related_name="mailings",
    )
    recipients = models.ManyToManyField(
        "clients.Recipient",
        verbose_name="Получатели",
        related_name="mailings",
        blank=False,
    )

    # Необязательное поле, чтобы отмечать факт отправки хотя бы раз
    last_sent_at = models.DateTimeField(
        "Последняя отправка",
        null=True,
        blank=True,
        help_text="Заполняется после первой реальной отправки.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Рассылка #{self.pk or '—'} — {self.status}"

    # --- Бизнес-логика статусов ---

    @property
    def is_sent_at_least_once(self) -> bool:
        return self.last_sent_at is not None

    def clean(self) -> None:
        super().clean()
        if self.end_at <= self.start_at:
            raise ValidationError({"end_at": "Окончание должно быть позже начала."})

    def compute_status(self) -> str:
        """Вычислить статус на текущий момент, не сохраняя модель."""
        now = timezone.now()
        if now >= self.end_at:
            return MailingStatus.FINISHED
        if self.is_sent_at_least_once or (self.start_at <= now < self.end_at):
            # Активна во временном окне ИЛИ уже была отправка -> Запущена
            return MailingStatus.RUNNING
        return MailingStatus.CREATED

    def refresh_status(self, save: bool = True) -> None:
        """Пересчитать и (опционально) сохранить статус."""
        new_status = self.compute_status()
        if self.status != new_status:
            self.status = new_status
            if save:
                super().save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        self.full_clean()
        # При первом сохранении по умолчанию "Создана"
        if not self.pk and not self.status:
            self.status = MailingStatus.CREATED
        super().save(*args, **kwargs)
        # После сохранения подправим статус согласно времени/флагам
        self.refresh_status(save=True)

class MailingLog(models.Model):
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name="Рассылка"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Когда")
    recipient = models.CharField(max_length=254, verbose_name="Кому (email)")
    status = models.CharField(max_length=32, verbose_name="Статус")  # SENT / ERROR / SKIPPED / DRY_RUN
    detail = models.TextField(blank=True, verbose_name="Детали")
    triggered_by = models.CharField(max_length=150, blank=True, null=True, verbose_name="Кем запущено")

    class Meta:
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправок"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"[{self.status}] {self.recipient} ({self.created_at:%Y-%m-%d %H:%M})"

class AttemptStatus(models.TextChoices):
    SUCCESS = "Успешно", "Успешно"
    FAIL = "Не успешно", "Не успешно"

class MailingAttempt(models.Model):
    """Попытка рассылки:
    - attempted_at: когда была попытка
    - status: Успешно / Не успешно
    - server_response: ответ почтового сервера или текст ошибки
    - mailing: FK на рассылку"""
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка"
    )
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата/время попытки")
    status = models.CharField(
        max_length=16, choices=AttemptStatus.choices, verbose_name="Статус"
    )
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ("-attempted_at",)
        indexes = [
            models.Index(fields=["mailing", "-attempted_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"[{self.status}] mailing={self.mailing_id} at {self.attempted_at:%Y-%m-%d %H:%M:%S}"

