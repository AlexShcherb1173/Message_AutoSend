from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class MailingStatus(models.TextChoices):
    """Перечисление возможных статусов рассылки.
    Значения:
        CREATED  ("Создана")   — объект создан, отправки ещё не начались.
        RUNNING  ("Запущена")  — рассылка активна: уже была хотя бы одна отправка
                                 или текущее время попадает в окно [start_at, end_at).
        FINISHED ("Завершена") — временное окно закончено (now >= end_at)."""
    CREATED = "Создана", "Создана"
    RUNNING = "Запущена", "Запущена"
    FINISHED = "Завершена", "Завершена"


class Mailing(models.Model):
    """Модель «Рассылка».
    Хранит временное окно рассылки (start_at/end_at), связанное сообщение и список
    получателей, а также служебные атрибуты для определения текущего статуса.
    Поля:
        start_at (DateTime): Дата/время первой возможной отправки.
        end_at (DateTime): Дата/время окончания окна рассылки. Должно быть > start_at.
        status (CharField): Текущий статус (см. MailingStatus). Поддерживается и
            автоматически пересчитывается методами модели.
        message (FK -> messages_app.Message): Сообщение, которое будет отправлено.
        recipients (M2M -> clients.Recipient): Получатели рассылки.
        last_sent_at (DateTime|null): Время фактической последней отправки. Если не
            пусто, считаем, что рассылка уже запускалась.
        created_at/updated_at (DateTime): Служебные временные метки.
    Бизнес-логика:
        - Валидация в clean(): end_at > start_at.
        - compute_status(): вычисляет статус «на сейчас», не изменяя модель.
        - refresh_status(): применяет вычисленный статус и опционально сохраняет.
        - save(): вызывает full_clean(), затем сохраняет и сразу подправляет статус,
          чтобы он соответствовал времени и флагам (например, last_sent_at).
    Замечание:
        Поле status — производное от времени и признака отправки. Пользовательский
        код может задавать его явно, но корректным источником истины считается
        compute_status(); для синхронизации используйте refresh_status()."""

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
        """Метаданные модели Mailing (человеко-читаемые имена и сортировка)."""
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Краткое строковое представление: «Рассылка #<id> — <статус>»."""
        return f"Рассылка #{self.pk or '—'} — {self.status}"

    # --- Бизнес-логика статусов ---

    @property
    def is_sent_at_least_once(self) -> bool:
        """Возвращает True, если рассылка уже выполнялась хотя бы один раз.
        Основано на наличии значения в last_sent_at."""
        return self.last_sent_at is not None

    def clean(self) -> None:
        """Выполняет валидацию полей модели перед сохранением.
        Проверки:
            - end_at > start_at
        Raises:
            ValidationError: если дата окончания не позже даты начала."""
        super().clean()
        if self.end_at <= self.start_at:
            raise ValidationError({"end_at": "Окончание должно быть позже начала."})

    def compute_status(self) -> str:
        """Вычислить статус рассылки «на текущий момент», не изменяя модель.
        Логика:
            - Если now >= end_at → FINISHED.
            - Если (start_at <= now < end_at) ИЛИ был хотя бы один факт отправки
              (is_sent_at_least_once) → RUNNING.
            - Иначе → CREATED.
        Returns:
            str: Одно из значений MailingStatus."""
        now = timezone.now()
        if now >= self.end_at:
            return MailingStatus.FINISHED
        if self.is_sent_at_least_once or (self.start_at <= now < self.end_at):
            # Активна во временном окне ИЛИ уже была отправка -> Запущена
            return MailingStatus.RUNNING
        return MailingStatus.CREATED

    def refresh_status(self, save: bool = True) -> None:
        """Пересчитать статус и при необходимости сохранить модель.
        Полезно вызывать после изменения временных полей или last_sent_at.
        Args:
            save (bool): Если True, сохраняет модель при изменении поля status.
        Side effects:
            Может вызвать сохранение модели (update_fields=["status", "updated_at"])."""
        new_status = self.compute_status()
        if self.status != new_status:
            self.status = new_status
            if save:
                super().save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        """Сохраняет объект с предварительной валидацией и актуализацией статуса.
        Порядок действий:
            1) full_clean() — гарантирует корректность дат.
            2) Если это первое сохранение и статус не задан — выставляется CREATED.
            3) Базовое сохранение super().save().
            4) Немедленная синхронизация статуса через refresh_status(save=True),
               чтобы status соответствовал окну времени и факту отправок.
        Примечание:
            Сохранение может происходить дважды: основное и возможное точечное
            обновление поля status (через update_fields)."""
        self.full_clean()
        # При первом сохранении по умолчанию "Создана"
        if not self.pk and not self.status:
            self.status = MailingStatus.CREATED
        super().save(*args, **kwargs)
        # После сохранения подправим статус согласно времени/флагам
        self.refresh_status(save=True)


class MailingLog(models.Model):
    """Лог события отправки по рассылке.
    Содержит простую запись о попытке/результате отправки одному получателю:
    кому отправляли, когда, итоговый статус и произвольные детали.
    Поля:
        mailing (FK -> Mailing): Связанная рассылка.
        created_at (DateTime): Когда зафиксировано событие.
        recipient (str): Адрес email получателя (snapshot на момент отправки).
        status (str): Результат шага (например, SENT/ERROR/SKIPPED/DRY_RUN).
        detail (Text): Доп. сведения (текст ошибки, ответ провайдера и т. п.).
        triggered_by (str|null): Идентификатор инициатора (username, job-id и т. п.)."""
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name="Рассылка"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Когда")
    recipient = models.CharField(max_length=254, verbose_name="Кому (email)")
    status = models.CharField(
        max_length=32,
        verbose_name="Статус",  # SENT / ERROR / SKIPPED / DRY_RUN
        help_text="Например: SENT, ERROR, SKIPPED, DRY_RUN.",
    )
    detail = models.TextField(blank=True, verbose_name="Детали")
    triggered_by = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Кем запущено"
    )

    class Meta:
        """Метаданные модели MailingLog (человеко-читаемые имена и сортировка)."""
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправок"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Человекочитаемая строка: «[STATUS] email (YYYY-MM-DD HH:MM)»."""
        return f"[{self.status}] {self.recipient} ({self.created_at:%Y-%m-%d %H:%M})"


class AttemptStatus(models.TextChoices):
    """Перечисление статусов попытки рассылки.
    Значения:
        SUCCESS ("Успешно")   — почтовый провайдер подтвердил отправку.
        FAIL    ("Не успешно") — попытка завершилась ошибкой."""
    SUCCESS = "Успешно", "Успешно"
    FAIL = "Не успешно", "Не успешно"


class MailingAttempt(models.Model):
    """Запись о попытке выполнения рассылки (агрегатный «трекер» отправки).
    Отличается от MailingLog тем, что описывает общий результат шага/итерации
    рассылки (например, запуск джобы или пачки писем), а не отправку
    конкретному получателю.
    Поля:
        mailing (FK -> Mailing): Рассылка, к которой относится попытка.
        attempted_at (DateTime, auto_now_add): Время фиксации попытки.
        status (AttemptStatus): Итоговый статус (успех/неуспех).
        server_response (Text): Свободный текст ответа провайдера/исключения.
    Индексы:
        - (mailing, -attempted_at): ускоряет запросы последних попыток по рассылке.
        - (status): выборка по итоговому статусу."""
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка"
    )
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата/время попытки")
    status = models.CharField(
        max_length=16, choices=AttemptStatus.choices, verbose_name="Статус"
    )
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")

    class Meta:
        """Метаданные модели MailingAttempt (человеко-читаемые имена, сортировка, индексы)."""
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ("-attempted_at",)
        indexes = [
            models.Index(fields=["mailing", "-attempted_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        """Краткая строка: «[STATUS] mailing=<id> at YYYY-MM-DD HH:MM:SS»."""
        return f"[{self.status}] mailing={self.mailing_id} at {self.attempted_at:%Y-%m-%d %H:%M:%S}"

