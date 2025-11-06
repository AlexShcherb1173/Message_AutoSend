from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional

from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from .models import Mailing, MailingLog, MailingAttempt, AttemptStatus


@dataclass
class SendResult:
    """Результат выполнения рассылки.
    Используется для возврата агрегированной статистики после вызова send_mailing().
    Атрибуты:
        total (int): Общее количество адресатов в рассылке.
        sent (int): Количество успешно отправленных писем.
        skipped (int): Количество пропущенных (ошибки, dry-run и т. д.)."""
    total: int
    sent: int
    skipped: int


def _iter_emails(mailing: Mailing) -> Iterable[tuple[str, str]]:
    """Генератор, возвращающий пары (email, recipient_name) для всех получателей рассылки.
    Параметры:
        mailing (Mailing): Экземпляр рассылки, из которого берутся связанные получатели.
    Возвращает:
        Iterable[tuple[str, str]]: Кортежи вида (email, name).
    Замечание:
        Предполагается, что модель Recipient содержит поля:
            - email (обязательный);
            - name или full_name (опциональный).
        При необходимости адаптируй под собственные имена полей."""
    for r in mailing.recipients.all():
        email: Optional[str] = getattr(r, "email", None)
        name: str = getattr(r, "name", "") or getattr(r, "full_name", "") or ""
        if email:
            yield (email, name)


def send_mailing(mailing: Mailing, *, user=None, dry_run: bool = False) -> SendResult:
    """Отправляет письма по выбранной рассылке через стандартный механизм Django.
    Универсальная функция для ручного запуска рассылки. Поддерживает «сухой» режим
    (dry_run) для тестирования и логирование каждой попытки через модель MailingAttempt.
    Параметры:
        mailing (Mailing): Экземпляр рассылки, подлежащий отправке.
        user (Optional[Any]): Пользователь или система, инициировавшая рассылку.
                              (Необязательный, сохраняется в логах, если требуется.)
        dry_run (bool): Если True — письма не отправляются реально, создаются
                        фиктивные записи о попытках с SUCCESS/DRY-RUN.
    Поведение:
        - Для каждого получателя извлекает email и имя (если есть).
        - Если dry_run=True — имитирует успешные попытки без реальной отправки.
        - Иначе вызывает send_mail() из django.core.mail, фиксируя результат.
        - При успешной отправке хотя бы одному адресату обновляет
          mailing.last_sent_at и актуализирует статус через refresh_status().
        - Для каждой попытки создаёт запись в MailingAttempt (SUCCESS/FAIL).
    Возвращает:
        SendResult: Объект со сводными счётчиками total / sent / skipped.
    Исключения:
        Все исключения при отправке перехватываются и регистрируются
        как попытки со статусом FAIL — функция не прерывает выполнение.
    Примечания:
        - В dev-среде можно использовать EMAIL_BACKEND =
          'django.core.mail.backends.console.EmailBackend' для вывода писем в консоль.
        - Предполагается, что у mailing.message есть поля subject и body."""
    recipient_emails = list(_iter_emails(mailing))
    total = len(recipient_emails)
    sent = 0
    skipped = 0

    # Предполагаем, что у сообщения есть поля subject/body (поправь при необходимости)
    subject = getattr(mailing.message, "subject", "Рассылка")
    body = getattr(mailing.message, "body", str(mailing.message))

    # Если не настроен EMAIL_BACKEND — в dev-режиме можно указать консольный backend
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    for email, name in recipient_emails:
        if dry_run:
            # Фиктивная запись — без реальной отправки
            MailingAttempt.objects.create(
                mailing=mailing,
                status=AttemptStatus.SUCCESS,
                server_response="DRY-RUN: письмо не отправлялось",
            )
            skipped += 1
            continue

        try:
            sent_count = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )
            if sent_count > 0:
                sent += 1
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status=AttemptStatus.SUCCESS,
                    server_response=f"send_mail returned {sent_count}",
                )
            else:
                skipped += 1
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status=AttemptStatus.FAIL,
                    server_response="send_mail returned 0",
                )
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            MailingAttempt.objects.create(
                mailing=mailing,
                status=AttemptStatus.FAIL,
                server_response=str(exc),
            )

    # Отмечаем факт хотя бы одной реальной отправки
    if not dry_run and sent > 0:
        mailing.last_sent_at = timezone.now()
        mailing.refresh_status(save=True)

    return SendResult(total=total, sent=sent, skipped=skipped)

