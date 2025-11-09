from __future__ import annotations

from django.core.management.base import BaseCommand
from mailings.tasks import run_due_mailings


class Command(BaseCommand):
    help = "Одноразово запускает отправку всех рассылок, которые пора отправить (по времени/статусу)."

    def handle(self, *args, **options):
        n = run_due_mailings(triggered_by="one-shot")
        self.stdout.write(self.style.SUCCESS(f"Done. Processed mailings: {n}"))