from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import AttemptStatus, Mailing, MailingAttempt, MailingLog

log = logging.getLogger("mailings")


@dataclass
class SendResult:
    """Агрегированный результат работы send_mailing()."""

    total: int = 0  # адресатов всего
    sent: int = 0  # реально отправлено
    skipped: int = 0  # пропущено/ошибки/DRY-RUN


def _iter_emails(mailing: Mailing) -> Iterable[tuple[str, str]]:
    """Кортежи (email, name) для всех получателей рассылки."""
    for r in mailing.recipients.all():
        email: Optional[str] = getattr(r, "email", None)
        name: str = getattr(r, "name", "") or getattr(r, "full_name", "") or ""
        if email:
            yield (email, name)


def send_mailing(
    mailing: Mailing,
    *,
    user=None,
    dry_run: bool = False,
    triggered_by: str | None = None,
) -> SendResult:
    """Ручной/плановый запуск рассылки.

    Пишем в БД:
      • MailingAttempt (агрегат по запуску) — с triggered_by;
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

    # инициатор: explicit triggered_by > user.email > пусто
    initiator = triggered_by
    if not initiator and user is not None:
        initiator = getattr(user, "email", None) or None

    # IMPORTANT: extra для форматтера логов (если он ждёт user_email)
    log_extra = {"user_email": initiator or "-"}

    log.info(
        "SEND start mailing_id=%s dry_run=%s total=%s subject=%r initiator=%s",
        mailing.pk,
        dry_run,
        total,
        subject,
        initiator or "-",
        extra=log_extra,
    )

    # Фиксируем факт «запуска попытки» (сначала FAIL, позже обновим на SUCCESS при успехе)
    attempt = MailingAttempt.objects.create(
        mailing=mailing,
        status=AttemptStatus.FAIL,
        server_response="attempt started",
        triggered_by=initiator,
    )
    log.debug(
        "ATTEMPT created attempt_id=%s mailing_id=%s",
        attempt.pk,
        mailing.pk,
        extra=log_extra,
    )

    try:
        for email, name in recipient_emails:
            if dry_run:
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=email,
                    status="DRY_RUN",
                    detail="Письмо не отправлялось (dry-run).",
                    triggered_by=initiator,
                )
                skipped += 1
                log.info(
                    "DRY-RUN skip mailing_id=%s to=%s",
                    mailing.pk,
                    email,
                    extra=log_extra,
                )
                continue

            try:
                log.debug(
                    "SMTP send try mailing_id=%s to=%s",
                    mailing.pk,
                    email,
                    extra=log_extra,
                )

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
                        triggered_by=initiator,
                    )
                    log.info(
                        "SENT ok mailing_id=%s to=%s",
                        mailing.pk,
                        email,
                        extra=log_extra,
                    )
                else:
                    skipped += 1
                    MailingLog.objects.create(
                        mailing=mailing,
                        recipient=email,
                        status="ERROR",
                        detail="send_mail вернул 0.",
                        triggered_by=initiator,
                    )
                    log.warning(
                        "SEND returned 0 mailing_id=%s to=%s",
                        mailing.pk,
                        email,
                        extra=log_extra,
                    )

            except Exception:  # noqa: BLE001
                skipped += 1
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=email,
                    status="ERROR",
                    detail="Exception during send (см. серверный лог).",
                    triggered_by=initiator,
                )
                log.exception(
                    "SEND fail mailing_id=%s to=%s", mailing.pk, email, extra=log_extra
                )

        # Итог по попытке + обновление mailing.last_sent_at
        if dry_run:
            attempt.status = AttemptStatus.SUCCESS
            attempt.server_response = f"dry-run; total={total}; skipped={skipped}"
        else:
            if sent > 0:
                attempt.status = AttemptStatus.SUCCESS
                attempt.server_response = f"sent={sent}; skipped={skipped}"

                # ВАЖНО: last_sent_at нужно сохранить в БД (иначе тесты и логика is_sent_at_least_once не сработают)
                mailing.last_sent_at = timezone.now()
                mailing.save(update_fields=["last_sent_at", "updated_at", "status"])
                # status в save() пересчитается через compute_status()
            else:
                attempt.status = AttemptStatus.FAIL
                attempt.server_response = f"no real sends; skipped={skipped}"

        attempt.save(update_fields=["status", "server_response"])
        log.debug(
            "ATTEMPT updated attempt_id=%s status=%s response=%s",
            attempt.pk,
            attempt.status,
            attempt.server_response,
            extra=log_extra,
        )

        dur_ms = int((time.perf_counter() - ts0) * 1000)
        log.info(
            "SEND done mailing_id=%s dry_run=%s duration_ms=%s total=%s sent=%s skipped=%s",
            mailing.pk,
            dry_run,
            dur_ms,
            total,
            sent,
            skipped,
            extra=log_extra,
        )
        return SendResult(total=total, sent=sent, skipped=skipped)

    except Exception:  # noqa: BLE001
        log.exception("SEND fatal mailing_id=%s", mailing.pk, extra=log_extra)
        try:
            attempt.status = AttemptStatus.FAIL
            attempt.server_response = "fatal error (см. серверный лог)"
            attempt.save(update_fields=["status", "server_response"])
        except Exception:  # noqa: BLE001
            log.exception(
                "ATTEMPT save fail (fatal) mailing_id=%s", mailing.pk, extra=log_extra
            )
        raise
