from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class MailingStatus(models.TextChoices):
    """Перечисление возможных статусов рассылки.

    Значения:
        CREATED  ("Создана")   — объект создан, отправки ещё не начались.
        RUNNING  ("Запущена")  — активна: было хотя бы одно отправление
                                 ИЛИ текущее время в окне [start_at, end_at).
        FINISHED ("Завершена") — временное окно завершено (now >= end_at).
    """
    CREATED = "Создана", "Создана"
    RUNNING = "Запущена", "Запущена"
    FINISHED = "Завершена", "Завершена"


class Mailing(models.Model):
    """Модель «Рассылка».

    Хранит окно рассылки (start_at/end_at), связанное сообщение и список
    получателей, а также поле `status` для быстрой фильтрации.
    Основной источник истины для статуса — метод `compute_status()`.

    Поля:
        start_at (DateTime): Дата/время первой возможной отправки.
        end_at (DateTime): Дата/время окончания окна рассылки (> start_at).
        status (CharField): Текущий статус (см. MailingStatus).
        message (FK -> messages_app.Message): Сообщение, которое будет отправлено.
        recipients (M2M -> clients.Recipient): Получатели рассылки.
        last_sent_at (DateTime|null): Время фактической последней отправки —
            если непусто, считаем, что рассылка запускалась.
        created_at/updated_at (DateTime): служебные метки.
    """

    start_at = models.DateTimeField("Дата/время первой отправки")
    end_at = models.DateTimeField("Дата/время окончания")
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=MailingStatus.choices,
        default=MailingStatus.CREATED,
        help_text="Текущий статус рассылки (автообновляется при сохранении).",
    )
    message = models.ForeignKey(
        "messages_app.Message",
        on_delete=models.PROTECT,  # чтобы не потерять текст письма в истории
        verbose_name="Сообщение",
        related_name="mailings",
    )
    recipients = models.ManyToManyField(
        "clients.Recipient",
        verbose_name="Получатели",
        related_name="mailings",
        blank=False,
        help_text="Список адресатов рассылки.",
    )

    # Необязательное поле — отметка факта отправки хотя бы раз
    last_sent_at = models.DateTimeField(
        "Последняя отправка",
        null=True,
        blank=True,
        help_text="Заполняется после первой реальной отправки.",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        """Метаданные модели Mailing (имена, сортировка, индексы, ограничения)."""
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
        ]

    def __str__(self) -> str:
        """Краткое строковое представление: «Рассылка #<id> — <статус> — <дата>»."""
        id_part = self.pk if self.pk is not None else "—"
        return f"Рассылка #{id_part} — {self.status} — {self.start_at:%Y-%m-%d %H:%M}"

    # --- Валидация и бизнес-логика статусов ---

    @property
    def is_sent_at_least_once(self) -> bool:
        """True, если рассылка выполнялась хотя бы один раз (по last_sent_at)."""
        return self.last_sent_at is not None

    def clean(self) -> None:
        """Выполняет валидацию полей модели перед сохранением.

        Проверки:
            - end_at > start_at
        """
        super().clean()
        if self.end_at and self.start_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "Окончание должно быть позже начала."})

    def compute_status(self) -> str:
        """Вычислить статус «на текущий момент», не изменяя модель.

        Логика:
            - Если now >= end_at → FINISHED.
            - Если (start_at <= now < end_at) ИЛИ уже была отправка → RUNNING.
            - Иначе → CREATED.
        """
        now = timezone.now()
        if self.end_at and now >= self.end_at:
            return MailingStatus.FINISHED
        if self.is_sent_at_least_once or (
            self.start_at and self.end_at and self.start_at <= now < self.end_at
        ):
            return MailingStatus.RUNNING
        return MailingStatus.CREATED

    def refresh_status(self, save: bool = True) -> None:
        """Пересчитать статус и при необходимости сохранить модель.

        Полезно вызывать после изменения временных полей или last_sent_at.
        """
        new_status = self.compute_status()
        if self.status != new_status:
            self.status = new_status
            if save:
                super().save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        """Сохранение с предварительной валидацией и синхронизацией статуса.

        Порядок:
            1) full_clean() — проверка корректности дат.
            2) Перед сохранением выставляем статус по compute_status().
            3) Сохраняем базовой реализацией.
        """
        self.full_clean()
        self.status = self.compute_status()
        return super().save(*args, **kwargs)


class MailingLog(models.Model):
    """Лог события отправки по рассылке.

    Хранит запись о попытке/результате отправки одному получателю:
    кому отправляли, когда, итоговый статус и произвольные детали.
    """

    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name="Рассылка"
    )
    created_at = models.DateTimeField("Когда", auto_now_add=True)
    recipient = models.CharField("Кому (email)", max_length=254)
    status = models.CharField(
        "Статус",
        max_length=32,
        help_text="Например: SENT, ERROR, SKIPPED, DRY_RUN.",
    )
    detail = models.TextField("Детали", blank=True)
    triggered_by = models.CharField(
        "Кем запущено", max_length=150, blank=True, null=True
    )

    class Meta:
        """Метаданные модели MailingLog (имена, сортировка, индексы)."""
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправок"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["mailing", "-created_at"], name="idx_log_mailing_created"),
            models.Index(fields=["status"], name="idx_log_status"),
            models.Index(fields=["recipient"], name="idx_log_recipient"),
        ]

    def __str__(self) -> str:
        """Человекочитаемая строка: «[STATUS] email (YYYY-MM-DD HH:MM)»."""
        return f"[{self.status}] {self.recipient} ({self.created_at:%Y-%m-%d %H:%M})"


class AttemptStatus(models.TextChoices):
    """Перечисление статусов попытки рассылки.

    Значения:
        SUCCESS ("Успешно")   — почтовый провайдер подтвердил отправку.
        FAIL    ("Не успешно") — попытка завершилась ошибкой.
    """
    SUCCESS = "Успешно", "Успешно"
    FAIL = "Не успешно", "Не успешно"


class MailingAttempt(models.Model):
    """Агрегированная запись о попытке выполнения рассылки.

    Описывает общий результат шага/итерации рассылки (например, запуск джобы или
    пачки писем), а не отправку конкретному получателю.
    """

    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка"
    )
    attempted_at = models.DateTimeField("Дата/время попытки", auto_now_add=True)
    status = models.CharField("Статус", max_length=16, choices=AttemptStatus.choices)
    server_response = models.TextField("Ответ почтового сервера", blank=True)

    class Meta:
        """Метаданные модели MailingAttempt (имена, сортировка, индексы)."""
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ("-attempted_at",)
        indexes = [
            models.Index(fields=["mailing", "-attempted_at"], name="idx_attempt_mailing_last"),
            models.Index(fields=["status"], name="idx_attempt_status"),
        ]

    def __str__(self) -> str:
        """Краткая строка: «[STATUS] mailing=<id> at YYYY-MM-DD HH:MM:SS»."""
        return f"[{self.status}] mailing={self.mailing_id} at {self.attempted_at:%Y-%m-%d %H:%M:%S}"

