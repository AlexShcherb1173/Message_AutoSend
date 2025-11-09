from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingLog, MailingAttempt, AttemptStatus
from clients.models import Recipient

log = logging.getLogger("mailings")


@dataclass
class SendResult:
    """Агрегированный результат работы send_mailing()."""
    total: int = 0    # адресатов всего
    sent: int = 0     # реально отправлено
    skipped: int = 0  # пропущено/ошибки/DRY-RUN


def _iter_emails(mailing: Mailing) -> Iterable[tuple[str, str]]:
    """Кортежи (email, name) для всех получателей рассылки."""
    for r in mailing.recipients.all():
        email: Optional[str] = getattr(r, "email", None)
        name: str = getattr(r, "name", "") or getattr(r, "full_name", "") or ""
        if email:
            yield (email, name)


def send_mailing(mailing: Mailing, *, user=None, dry_run: bool = False) -> SendResult:
    """
    Ручной/плановый запуск рассылки.

    Логируем:
      • старт/завершение отправки (с длительностью);
      • каждую попытку отправки (в т.ч. DRY-RUN);
      • исключения (с трейсбеком);
      • сводку (total/sent/skipped).

    Пишем в БД:
      • MailingAttempt (агрегат по запуску) — с пометкой triggered_by;
      • MailingLog на каждого адресата — статусы: SENT / ERROR / DRY_RUN.
    """
    ts0 = time.perf_counter()

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

    log.info(
        "SEND start mailing_id=%s dry_run=%s total=%s subject=%r initiator=%s",
        mailing.pk, dry_run, total, subject, initiator or "-",
    )

    # Фиксируем факт «запуска попытки» (сначала ставим FAIL, позже обновим)
    attempt = MailingAttempt.objects.create(
        mailing=mailing,
        status=AttemptStatus.FAIL,  # обновим на SUCCESS по факту
        server_response="attempt started",
        triggered_by=initiator or None,
    )
    log.debug("ATTEMPT created attempt_id=%s mailing_id=%s", attempt.pk, mailing.pk)

    try:
        for email, name in recipient_emails:
            if dry_run:
                # Тест: письмо не отправляется
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=email,
                    status="DRY_RUN",
                    detail="Письмо не отправлялось (dry-run).",
                    triggered_by=initiator or None,
                )
                skipped += 1
                log.info("DRY-RUN skip mailing_id=%s to=%s", mailing.pk, email)
                continue

            try:
                log.debug("SMTP send try mailing_id=%s to=%s", mailing.pk, email)
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
                    log.info("SENT ok mailing_id=%s to=%s", mailing.pk, email)
                else:
                    skipped += 1
                    MailingLog.objects.create(
                        mailing=mailing,
                        recipient=email,
                        status="ERROR",
                        detail="send_mail вернул 0.",
                        triggered_by=initiator or None,
                    )
                    log.warning("SEND returned 0 mailing_id=%s to=%s", mailing.pk, email)

            except Exception:  # noqa: BLE001
                skipped += 1
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=email,
                    status="ERROR",
                    detail="Exception during send (см. серверный лог).",
                    triggered_by=initiator or None,
                )
                log.exception("SEND fail mailing_id=%s to=%s", mailing.pk, email)

        # Пересчитываем статус попытки
        if dry_run:
            attempt.status = AttemptStatus.SUCCESS
            attempt.server_response = f"dry-run; total={total}; skipped={skipped}"
        else:
            if sent > 0:
                attempt.status = AttemptStatus.SUCCESS
                attempt.server_response = f"sent={sent}; skipped={skipped}"
                mailing.last_sent_at = timezone.now()
                mailing.refresh_status(save=True)
            else:
                attempt.status = AttemptStatus.FAIL
                attempt.server_response = f"no real sends; skipped={skipped}"

        attempt.save(update_fields=["status", "server_response"])
        log.debug(
            "ATTEMPT updated attempt_id=%s status=%s response=%s",
            attempt.pk, attempt.status, attempt.server_response,
        )

        dur_ms = int((time.perf_counter() - ts0) * 1000)
        log.info(
            "SEND done mailing_id=%s dry_run=%s duration_ms=%s total=%s sent=%s skipped=%s",
            mailing.pk, dry_run, dur_ms, total, sent, skipped,
        )
        return SendResult(total=total, sent=sent, skipped=skipped)

    except Exception:
        # Фатальная ошибка всего запуска
        log.exception("SEND fatal mailing_id=%s", mailing.pk)
        try:
            attempt.status = AttemptStatus.FAIL
            attempt.server_response = "fatal error (см. серверный лог)"
            attempt.save(update_fields=["status", "server_response"])
        except Exception:
            log.exception("ATTEMPT save fail (fatal) mailing_id=%s", mailing.pk)
        raise

