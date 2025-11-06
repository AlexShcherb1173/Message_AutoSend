from __future__ import annotations
from django.core.management.base import BaseCommand, CommandError

from mailings.models import Mailing
from mailings.services import send_mailing


class Command(BaseCommand):
    help = "Отправить рассылку вручную по её ID."

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID рассылки")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только симуляция отправки, без реальной доставки.",
        )

    def handle(self, *args, **options):
        pk = options["mailing_id"]
        dry_run = options["dry_run"]

        try:
            mailing = Mailing.objects.get(pk=pk)
        except Mailing.DoesNotExist as exc:
            raise CommandError(f"Рассылка с id={pk} не найдена") from exc

        result = send_mailing(mailing, user=None, dry_run=dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY-RUN: всего={result.total}, отправлено бы={result.total}, реально=0"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"ГОТОВО: всего={result.total}, отправлено={result.sent}, пропущено/ошибок={result.skipped}"
            ))