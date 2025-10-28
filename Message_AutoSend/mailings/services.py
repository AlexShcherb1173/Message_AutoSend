from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional

from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from .models import Mailing, MailingLog, MailingAttempt, AttemptStatus


@dataclass
class SendResult:
    total: int
    sent: int
    skipped: int


def _iter_emails(mailing: Mailing) -> Iterable[tuple[str, str]]:
    """Возвращает пары (email, recipient_name) для всех получателей рассылки.
    Правь под свои поля модели Recipient."""
    for r in mailing.recipients.all():
        email: Optional[str] = getattr(r, "email", None)
        name: str = getattr(r, "name", "") or ""
        if email:
            yield (email, name)


def send_mailing(mailing: Mailing, *, user=None, dry_run: bool = False) -> SendResult:
    """Ручная отправка рассылки по email. Можно расширить для SMS/мессенджеров.
    - Если dry_run=True, ничего не отправляет, только считает.
    - При успехе проставляет last_sent_at и обновляет статус."""
    recipient_emails = list(_iter_emails(mailing))
    total = len(recipient_emails)
    sent = 0
    skipped = 0

    # предполагаем, что у сообщения есть поля subject/body (поправь при необходимости)
    subject = getattr(mailing.message, "subject", "Рассылка")
    body = getattr(mailing.message, "body", str(mailing.message))

    # если не настроен EMAIL_BACKEND — в dev-режиме можно указать 'django.core.mail.backends.console.EmailBackend'
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    for email, name in recipient_emails:
        if dry_run:
            MailingAttempt.objects.create(
                mailing=mailing,
                status=AttemptStatus.SUCCESS,  # симулируем успешную попытку
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

    # отметим факт отправки хотя бы раз
    if not dry_run and sent > 0:
        mailing.last_sent_at = timezone.now()
        mailing.refresh_status(save=True)

    return SendResult(total=total, sent=sent, skipped=skipped)

