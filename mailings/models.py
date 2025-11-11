from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Count, Q


class MailingStatus(models.TextChoices):
    """Возможные статусы рассылки.
    CREATED  ("Создана")   — объект создан, отправки ещё не начались.
    RUNNING  ("Запущена")  — активна: было хотя бы одно отправление ИЛИ текущее время в окне.
    FINISHED ("Завершена") — временное окно завершено."""

    CREATED = "Создана", "Создана"
    RUNNING = "Запущена", "Запущена"
    FINISHED = "Завершена", "Завершена"


# ====== Статистический QuerySet/Manager по рассылкам (агрегаты для списков/админки) ======
class MailingQuerySet(models.QuerySet):
    """
    QS с аннотациями сводной статистики по логам и попыткам.

    Аннотации (int):
      - sent_messages:    кол-во логов со status='SENT'        (реально ушедшие письма)
      - failed_messages:  кол-во логов со status='ERROR'       (ошибки на письмах)
      - dry_run_messages: кол-во логов со status='DRY_RUN'     (тестовые «псевдо»-отправки)
      - attempt_success:  кол-во попыток со статусом 'Успешно'
      - attempt_fail:     кол-во попыток со статусом 'Не успешно'
    """

    def with_stats(self) -> "MailingQuerySet":
        return self.annotate(
            sent_messages=Count("logs", filter=Q(logs__status="SENT")),
            failed_messages=Count("logs", filter=Q(logs__status="ERROR")),
            dry_run_messages=Count("logs", filter=Q(logs__status="DRY_RUN")),
            attempt_success=Count("attempts", filter=Q(attempts__status="Успешно")),
            attempt_fail=Count("attempts", filter=Q(attempts__status="Не успешно")),
        )


class MailingManager(models.Manager.from_queryset(MailingQuerySet)):
    """Менеджер, отдающий расширенный QuerySet (with_stats)."""

    pass


class Mailing(models.Model):
    """
    «Рассылка» — окно времени, сообщение, список получателей, статус и владелец.
    Поле owner — кто создал рассылку; используется для ограничения доступа.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mailings",
        verbose_name="Владелец",
        help_text="Пользователь-владелец этой рассылки.",
    )

    start_at = models.DateTimeField("Дата/время первой отправки")
    end_at = models.DateTimeField("Дата/время окончания")

    status = models.CharField(
        "Статус",
        max_length=16,
        choices=MailingStatus.choices,
        default=MailingStatus.CREATED,
        help_text="Авторассчитывается при сохранении (см. compute_status()).",
    )

    message = models.ForeignKey(
        "messages_app.Message",
        on_delete=models.PROTECT,  # бережём историю писем
        verbose_name="Сообщение",
        related_name="mailings",
    )
    recipients = models.ManyToManyField(
        "clients.Recipient",
        verbose_name="Получатели",
        related_name="mailings",
        blank=False,
        help_text="Кому отправляем.",
    )

    last_sent_at = models.DateTimeField(
        "Последняя отправка",
        null=True,
        blank=True,
        help_text="Ставитcя после первой реальной отправки.",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    # Подключаем кастомный менеджер
    objects: MailingManager = MailingManager()

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ("-start_at", "-id")
        constraints = [
            models.CheckConstraint(
                name="mailing_end_after_start",
                check=models.Q(end_at__gt=models.F("start_at")),
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="idx_mailing_status"),
            models.Index(fields=["start_at"], name="idx_mailing_start"),
            models.Index(fields=["end_at"], name="idx_mailing_end"),
            models.Index(fields=["-created_at"], name="idx_mailing_created_desc"),
            models.Index(fields=["owner"], name="idx_mailing_owner"),
        ]
        # Кастомные права для группы «Менеджеры»
        permissions = (
            ("view_all_mailings", "Может просматривать все рассылки"),
            ("disable_mailing", "Может отключать (завершать) рассылки"),
        )

    def __str__(self) -> str:
        return f"Рассылка #{self.pk or '—'} — {self.status} — {self.start_at:%Y-%m-%d %H:%M}"

    # ---- «Глобальные» свойства статистики (для одной рассылки) ----
    @property
    def stat_sent_messages(self) -> int:
        """Сколько писем реально отправлено (по логам со статусом SENT)."""
        return int(getattr(self, "sent_messages", 0) or 0)

    @property
    def stat_failed_messages(self) -> int:
        """Сколько писем завершилось ошибкой (по логам со статусом ERROR)."""
        return int(getattr(self, "failed_messages", 0) or 0)

    @property
    def stat_dry_run_messages(self) -> int:
        """Сколько «отправок» пришлось на DRY-RUN (не реальная почта)."""
        return int(getattr(self, "dry_run_messages", 0) or 0)

    @property
    def stat_attempt_success(self) -> int:
        """Сколько батч-попыток (агрег.) успешно выполнено."""
        return int(getattr(self, "attempt_success", 0) or 0)

    @property
    def stat_attempt_fail(self) -> int:
        """Сколько батч-попыток (агрег.) завершилось ошибкой."""
        return int(getattr(self, "attempt_fail", 0) or 0)

    def stats_dict(self) -> dict[str, int]:
        """Компактный словарь «общей» статистики по рассылке (для шаблонов)."""
        return {
            "sent_messages": self.stat_sent_messages,
            "failed_messages": self.stat_failed_messages,
            "dry_run_messages": self.stat_dry_run_messages,
            "attempt_success": self.stat_attempt_success,
            "attempt_fail": self.stat_attempt_fail,
        }

    # ---- Бизнес-логика статусов ----
    @property
    def is_sent_at_least_once(self) -> bool:
        """True, если рассылка запускалась (по last_sent_at)."""
        return self.last_sent_at is not None

    def clean(self) -> None:
        """Базовая валидация полей."""
        super().clean()
        if self.end_at and self.start_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "Окончание должно быть позже начала."})

    def compute_status(self) -> str:
        """Посчитать статус на «сейчас», не сохраняя модель."""
        now = timezone.now()
        if self.end_at and now >= self.end_at:
            return MailingStatus.FINISHED
        if self.is_sent_at_least_once or (
            self.start_at and self.end_at and self.start_at <= now < self.end_at
        ):
            return MailingStatus.RUNNING
        return MailingStatus.CREATED

    def refresh_status(self, save: bool = True) -> None:
        """Пересчитать status и опционально сохранить."""
        new_status = self.compute_status()
        if self.status != new_status:
            self.status = new_status
            if save:
                super().save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        """Валидация + синхронизация статуса перед сохранением."""
        self.full_clean()
        self.status = self.compute_status()
        return super().save(*args, **kwargs)


class MailingLog(models.Model):
    """
    Лог по каждому получателю (почтовая «телеметрия»).

    Важный момент: поле `triggered_by` хранит «кто инициировал отправку»
    (обычно email пользователя). На основании этого считаем персональные отчёты.
    """

    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name="Рассылка"
    )
    created_at = models.DateTimeField("Когда", auto_now_add=True)
    recipient = models.CharField("Кому (email)", max_length=254)
    status = models.CharField(
        "Статус",
        max_length=32,  # Например: SENT, ERROR, SKIPPED, DRY_RUN
        help_text="Например: SENT, ERROR, SKIPPED, DRY_RUN.",
    )
    detail = models.TextField("Детали", blank=True)
    triggered_by = models.CharField(
        "Кем запущено",
        max_length=150,
        blank=True,
        null=True,
        help_text="Идентификатор инициатора (обычно email пользователя).",
    )

    class Meta:
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправок"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["mailing", "-created_at"], name="idx_log_mailing_created"
            ),
            models.Index(fields=["status"], name="idx_log_status"),
            models.Index(fields=["recipient"], name="idx_log_recipient"),
            models.Index(fields=["triggered_by"], name="idx_log_triggered_by"),
        ]

    def __str__(self) -> str:
        return f"[{self.status}] {self.recipient} ({self.created_at:%Y-%m-%d %H:%M})"


class AttemptStatus(models.TextChoices):
    """Статусы агрегированной попытки."""

    SUCCESS = "Успешно", "Успешно"
    FAIL = "Не успешно", "Не успешно"


class MailingAttempt(models.Model):
    """
    Агрегированная попытка выполнения рассылки (батч/итерация, а не конкретный адресат).

    Поле `triggered_by` фиксирует инициатора попытки (по email/логину),
    чтобы формировать персональные отчёты без связи на User.
    """

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )
    attempted_at = models.DateTimeField("Дата/время попытки", auto_now_add=True)
    status = models.CharField("Статус", max_length=16, choices=AttemptStatus.choices)
    server_response = models.TextField("Ответ почтового сервера", blank=True)
    triggered_by = models.CharField(
        "Кем запущено",
        max_length=150,
        blank=True,
        null=True,
        help_text="Идентификатор инициатора (обычно email пользователя).",
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ("-attempted_at",)
        indexes = [
            models.Index(
                fields=["mailing", "-attempted_at"], name="idx_attempt_mailing_last"
            ),
            models.Index(fields=["status"], name="idx_attempt_status"),
            models.Index(fields=["triggered_by"], name="idx_attempt_triggered_by"),
        ]

    def __str__(self) -> str:
        return f"[{self.status}] mailing={self.mailing_id} at {self.attempted_at:%Y-%m-%d %H:%M:%S}"
