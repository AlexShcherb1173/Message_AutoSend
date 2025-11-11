from __future__ import annotations

import logging
import signal
import sys

from django.core.management.base import BaseCommand
from django.utils import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import (
    DjangoJobStore,
    register_events,
    DjangoJobExecution,
)
from django_apscheduler import util as aps_util

from mailings.tasks import run_due_mailings


# Получаем именованный логгер — он пишет в logs/scheduler/ и общий app.log
logger = logging.getLogger(__name__)


@aps_util.close_old_connections
def job_send_due_mailings():
    """Фоновая задача планировщика APS.
    Назначение:
      - Проверяет и отправляет рассылки, для которых наступило время отправки.
      - Вызывает функцию run_due_mailings(), которая возвращает количество обработанных рассылок.
      - Логирует количество отправленных кампаний (в INFO-уровне).
    Декоратор @close_old_connections — автоматически закрывает старые DB-сессии
    между вызовами (рекомендация из django-apscheduler)."""
    processed = run_due_mailings(triggered_by="apscheduler")
    logger.info("APS: processed mailings: %s", processed)


@aps_util.close_old_connections
def job_cleanup_old_executions(max_age_seconds: int = 60 * 60 * 24 * 7):
    """Служебная задача очистки старых записей об исполнениях job'ов.
        Параметры:
        max_age_seconds: int
            Максимальный "возраст" записей о выполнении (по умолчанию 7 дней).
    DjangoJobExecution хранит историю выполнений задач APS.
    Если её не чистить, база может разрастись."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age=max_age_seconds)
    logger.info("APS: old job executions cleared (max_age=%s sec)", max_age_seconds)


class Command(BaseCommand):
    """Django management-команда: run_scheduler
    Запускает фоновый планировщик APScheduler, который:
      • каждые N секунд проверяет, есть ли рассылки, готовые к отправке;
      • раз в сутки очищает историю старых выполнений задач.
    Пример запуска:
        python manage.py run_scheduler --interval 60
    Используется внутри PowerShell/Batch-скриптов:
        scripts/run_scheduler.ps1
        scripts/run_scheduler.bat
    Работает до прерывания процесса (Ctrl+C / SIGTERM)."""

    help = "Запускает фонового планировщика (APS) для автоматической отправки рассылок."

    def add_arguments(self, parser):
        """Добавляем аргумент --interval:
        интервал (в секундах) между проверками отложенных рассылок."""
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Интервал в секундах между проверками 'должных' рассылок (по умолчанию 60 сек.)",
        )

    def handle(self, *args, **options):
        """Основной обработчик команды.
        1. Инициализирует планировщик APScheduler.
        2. Подключает DjangoJobStore (чтобы хранить задачи и результаты в БД).
        3. Регистрирует две задачи:
           - job_send_due_mailings — отправка рассылок (каждые interval секунд);
           - job_cleanup_old_executions — очистка истории job'ов (каждые 24 часа).
        4. Добавляет слушатели событий (ошибки, завершения, next run time и т.п.).
        5. Запускает scheduler.start() и держит процесс живым, пока не придёт сигнал завершения.
        """

        interval = options["interval"]
        tz = timezone.get_current_timezone()

        # Инициализация планировщика с учётом текущей таймзоны Django
        scheduler = BackgroundScheduler(timezone=tz)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # --- Регулярная задача: проверка и отправка рассылок ---
        scheduler.add_job(
            job_send_due_mailings,
            trigger=IntervalTrigger(seconds=interval),
            id="mailings_send_due",
            max_instances=1,  # не более 1 экземпляра одновременно
            replace_existing=True,  # заменять старую версию задачи, если перезапущено
            jobstore="default",
            coalesce=True,  # если несколько тиков пропущены — объединяем
            misfire_grace_time=30,  # допустимое опоздание (в секундах)
        )

        # --- Ежедневная очистка истории job-исполнений ---
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

        # Подписываемся на системные события планировщика (для логирования ошибок и т.д.)
        register_events(scheduler)

        self.stdout.write(self.style.SUCCESS("Starting APScheduler..."))
        logger.info("APScheduler started (interval=%s sec)", interval)

        scheduler.start()

        # --- Грейсфул-шатдаун по Ctrl+C / SIGTERM ---
        def shutdown(signum=None, frame=None):
            """Завершает планировщик при получении сигнала остановки.
            Корректно закрывает соединения и завершает процесс без ошибок."""
            self.stdout.write("\nStopping scheduler...")
            logger.info("APScheduler stopped by signal %s", signum)
            scheduler.shutdown(wait=False)
            sys.exit(0)

        # SIGINT = Ctrl+C, SIGTERM = kill/stop
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        # --- Блокировка основного потока ---
        try:
            # На UNIX можно "заморозить" цикл, слушая сигналы
            while True:
                signal.pause()
        except AttributeError:
            # На Windows signal.pause() отсутствует — используем вечный sleep
            import time

            while True:
                time.sleep(60)
