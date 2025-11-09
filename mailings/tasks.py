from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import Mailing, MailingStatus
from .services import send_mailing


LOCK_KEY = "mailings:runner:lock"
LOCK_TTL = 55  # сек — чтобы job раз в минуту не накладывались друг на друга


def _acquire_lock() -> bool:
    # Redis-кеш add вернёт True, если ключа не было — значит, мы захватили «мьютекс»
    return cache.add(LOCK_KEY, "1", timeout=LOCK_TTL)


def _release_lock() -> None:
    cache.delete(LOCK_KEY)


def due_mailings_queryset() -> Iterable[Mailing]:
    """
    Возвращает рассылки, которые попали в окно отправки.
    По умолчанию — старт <= сейчас <= конец и статус «создана/запущена».
    Чтобы избежать слишком частого повторного пинка, проверяем last_sent_at.
    """
    now = timezone.now()
    min_repeat = getattr(settings, "MAILINGS_MIN_REPEAT_MINUTES", 5)
    cutoff = now - timedelta(minutes=min_repeat)

    qs = (
        Mailing.objects.filter(
            start_at__lte=now,
            end_at__gte=now,
            status__in=[MailingStatus.CREATED, MailingStatus.RUNNING],
        )
        .select_related("message", "owner")
        .prefetch_related("recipients")
    )

    # если есть last_sent_at — пропустим, пока не пройдёт «анти-флуд» окно
    qs = qs.filter(
        # либо ещё не отправляли,
        (Q(last_sent_at__isnull=True)) |
        # либо отправляли давно
        Q(last_sent_at__lte=cutoff)
    )

    return qs


def run_due_mailings(triggered_by: str = "scheduler") -> int:
    """
    Основная функция: отправляет все «должные» рассылки.
    Возвращает количество обработанных рассылок.
    """
    if not _acquire_lock():
        # другая копия уже работает — выходим тихо
        return 0

    processed = 0
    try:
        for mailing in due_mailings_queryset():
            # send_mailing сам запишет логи/попытки; здесь просто вызываем
            send_mailing(mailing, user=mailing.owner, dry_run=False, triggered_by=triggered_by)
            # актуализируем статус и отметим время последней отправки
            mailing.refresh_status(save=True)
            processed += 1
        return processed
    finally:
        _release_lock()