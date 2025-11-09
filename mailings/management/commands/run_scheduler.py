from __future__ import annotations

import logging
import signal
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events, DjangoJobExecution
from django_apscheduler import util as aps_util

from mailings.tasks import run_due_mailings

logger = logging.getLogger(__name__)


@aps_util.close_old_connections
def job_send_due_mailings():
    processed = run_due_mailings(triggered_by="apscheduler")
    logger.info("APS: processed mailings: %s", processed)


@aps_util.close_old_connections
def job_cleanup_old_executions(max_age_seconds: int = 60 * 60 * 24 * 7):
    """
    Чистим историю выполнений джоб (по умолчанию — неделя).
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age=max_age_seconds)


class Command(BaseCommand):
    help = "Запускает фонового планировщика (APS) для автоматической отправки рассылок."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Интервал в секундах между проверками 'должных' рассылок (по умолчанию 60 сек.)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        tz = timezone.get_current_timezone()

        scheduler = BackgroundScheduler(timezone=tz)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Регулярная задача: проверять и отправлять рассылки
        scheduler.add_job(
            job_send_due_mailings,
            trigger=IntervalTrigger(seconds=interval),
            id="mailings_send_due",
            max_instances=1,
            replace_existing=True,
            jobstore="default",
            coalesce=True,
            misfire_grace_time=30,
        )

        # Периодическая уборка истории job-исполнений (раз в день)
        scheduler.add_job(
            job_cleanup_old_executions,
            trigger=IntervalTrigger(hours=24),
            id="aps_cleanup",
            max_instances=1,
            replace_existing=True,
            jobstore="default",
            coalesce=True,
            misfire_grace_time=60,
        )

        # Листенеры событий (логирование ошибок и т.д.)
        register_events(scheduler)

        self.stdout.write(self.style.SUCCESS("Starting APScheduler..."))
        scheduler.start()

        # Аккуратное завершение по Ctrl+C / SIGTERM
        def shutdown(signum=None, frame=None):
            self.stdout.write("\nStopping scheduler...")
            scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        # Блокируем поток (держим процесс живым)
        try:
            while True:
                signal.pause()
        except AttributeError:
            # Windows: у signal нет pause — заменим на бесконечный цикл с sleep
            import time
            while True:
                time.sleep(60)