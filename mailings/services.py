from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional

from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from .models import Mailing, MailingLog, MailingAttempt, AttemptStatus


@dataclass
class SendResult:
    """Агрегированный результат работы send_mailing()."""
    total: int   # адресатов всего
    sent: int    # реально отправлено
    skipped: int # пропущено/ошибки/DRY-RUN


def _iter_emails(mailing: Mailing) -> Iterable[tuple[str, str]]:
    """Кортежи (email, name) для всех получателей рассылки."""
    for r in mailing.recipients.all():
        email: Optional[str] = getattr(r, "email", None)
        name: str = getattr(r, "name", "") or getattr(r, "full_name", "") or ""
        if email:
            yield (email, name)


def send_mailing(mailing: Mailing, *, user=None, dry_run: bool = False) -> SendResult:
    """Ручной запуск рассылки.

    Пишем:
      • MailingAttempt (агрегат по запуску) — с пометкой initiated_by
      • MailingLog на каждого адресата — со статусом SENT / ERROR / DRY_RUN
        и с пометкой triggered_by (email инициатора).

    Эти данные используются для персональных отчётов по пользователям.
    """
    recipient_emails = list(_iter_emails(mailing))
    total = len(recipient_emails)
    sent = 0
    skipped = 0

    subject = getattr(mailing.message, "subject", "Рассылка")
    body = getattr(mailing.message, "body", str(mailing.message))
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    initiator = ""
    if user and getattr(user, "email", None):
        initiator = user.email

    # Фиксируем сам факт «запуска попытки» (сначала предполагаем FAIL, потом обновим)
    attempt = MailingAttempt.objects.create(
        mailing=mailing,
        status=AttemptStatus.FAIL,  # обновим на SUCCESS по факту
        server_response="attempt started",
        triggered_by=initiator or None,
    )

    for email, name in recipient_emails:
        if dry_run:
            # Тест: логируем DRY_RUN (письмо не отправлялось)
            MailingLog.objects.create(
                mailing=mailing,
                recipient=email,
                status="DRY_RUN",
                detail="Письмо не отправлялось (dry-run).",
                triggered_by=initiator or None,
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
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=email,
                    status="SENT",
                    detail="Отправлено стандартным SMTP backend.",
                    triggered_by=initiator or None,
                )
            else:
                skipped += 1
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=email,
                    status="ERROR",
                    detail="send_mail вернул 0.",
                    triggered_by=initiator or None,
                )
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            MailingLog.objects.create(
                mailing=mailing,
                recipient=email,
                status="ERROR",
                detail=str(exc),
                triggered_by=initiator or None,
            )

    # Пересчитываем статус попытки: успех, если было хоть одно реальное отправление
    if not dry_run and sent > 0:
        attempt.status = AttemptStatus.SUCCESS
        attempt.server_response = f"sent={sent}; skipped={skipped}"
        attempt.save(update_fields=["status", "server_response"])
        mailing.last_sent_at = timezone.now()
        mailing.refresh_status(save=True)
    else:
        attempt.status = AttemptStatus.FAIL if not dry_run else AttemptStatus.SUCCESS
        attempt.server_response = (
            "dry-run (ok)" if dry_run else f"no real sends; skipped={skipped}"
        )
        attempt.save(update_fields=["status", "server_response"])

    return SendResult(total=total, sent=sent, skipped=skipped)

