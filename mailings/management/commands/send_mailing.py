"""
Команда Django `send_mailing` — ручной запуск рассылки по её ID.

Назначение:
    Позволяет администратору или разработчику отправить рассылку вручную
    из консоли Django по заданному ID (pk) модели `Mailing`.

Функциональность:
    - Проверяет наличие рассылки в базе данных.
    - Запускает сервис отправки (`send_mailing`) с передачей объекта рассылки.
    - Поддерживает режим `--dry-run`, в котором выполнение имитируется без реальной отправки писем.
    - Выводит статистику по результатам: сколько писем было бы отправлено, отправлено реально или пропущено.

Использование:
    python manage.py send_mailing <id>
    python manage.py send_mailing <id> --dry-run

Пример:
    python manage.py send_mailing 3
    python manage.py send_mailing 2 --dry-run

Результат:
    ✅ ГОТОВО: всего=15, отправлено=15, пропущено/ошибок=0
    или
    ⚠️ DRY-RUN: всего=15, отправлено бы=15, реально=0
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from mailings.models import Mailing
from mailings.services import send_mailing


class Command(BaseCommand):
    """
    Команда `send_mailing` — отправляет рассылку вручную по ID.

    Аргументы:
        mailing_id (int): первичный ключ рассылки.
        --dry-run (flag): если указан, выполняется имитация рассылки
                          без фактической доставки писем.

    Поведение:
        1. Проверяет, существует ли рассылка с заданным ID.
        2. Если не найдена — выбрасывает CommandError.
        3. Запускает функцию `send_mailing()` (реальный механизм отправки).
        4. После завершения печатает итоговую статистику.
    """

    help = "Отправить рассылку вручную по её ID."

    def add_arguments(self, parser):
        """
        Определяет аргументы командной строки для вызова команды.

        Args:
            parser (ArgumentParser): объект парсера команд Django.
        """
        parser.add_argument(
            "mailing_id",
            type=int,
            help="ID рассылки, которую необходимо отправить."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только симуляция отправки, без реальной доставки (DRY-RUN режим)."
        )

    def handle(self, *args, **options):
        """
        Основной метод, выполняющий бизнес-логику команды.

        Args:
            *args: позиционные аргументы (не используются).
            **options: параметры, переданные из командной строки.

        Raises:
            CommandError: если рассылка с указанным ID не найдена.
        """
        pk = options["mailing_id"]
        dry_run = options["dry_run"]

        # --- Проверяем наличие рассылки ---
        try:
            mailing = Mailing.objects.get(pk=pk)
        except Mailing.DoesNotExist as exc:
            raise CommandError(f"❌ Рассылка с id={pk} не найдена.") from exc

        # --- Запускаем сервис отправки (или имитацию) ---
        result = send_mailing(mailing, user=None, dry_run=dry_run)

        # --- Вывод результата ---
        if dry_run:
            # В режиме dry-run показываем только статистику симуляции
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ DRY-RUN: всего={result.total}, "
                    f"отправлено бы={result.total}, реально=0"
                )
            )
        else:
            # В реальном режиме показываем реальный результат
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ ГОТОВО: всего={result.total}, "
                    f"отправлено={result.sent}, "
                    f"пропущено/ошибок={result.skipped}"
                )
            )