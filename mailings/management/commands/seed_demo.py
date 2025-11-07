"""
Команда `seed_demo` — наполнение БД демонстрационными данными (получатели, сообщения, рассылки)
из штатных фикстур. Предусмотрен безопасный режим и очистка таблиц.

Использование:
    python manage.py seed_demo
    python manage.py seed_demo --flush
    python manage.py seed_demo --verbosity 2

По умолчанию команда подхватывает фикстуры из стандартных каталогов apps:
- clients/fixtures/recipients.json
- messages_app/fixtures/messages.json
- mailing/fixtures/mailings.json

После загрузки фикстур выполняется пересчёт статусов у рассылок.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone

from clients.models import Recipient
from messages_app.models import Message
from mailings.models import Mailing


class Command(BaseCommand):
    help = "Загрузить демонстрационные данные (fixtures) для клиентов, сообщений и рассылок."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Очистить связанные таблицы перед загрузкой фикстур.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        flush = options.get("flush", False)

        if flush:
            self.stdout.write(self.style.WARNING("▶ Очищаем таблицы..."))
            # порядок важен из-за FK/M2M
            Mailing.objects.all().delete()
            Message.objects.all().delete()
            Recipient.objects.all().delete()

        self.stdout.write(self.style.NOTICE("▶ Загружаем фикстуры..."))
        # Имена без путей — Django сам найдёт в <app>/fixtures/
        # Можно запускать повторно: PK-конфликты не возникнут, если перед этим делали --flush.
        call_command("loaddata", "recipients", verbosity=0)
        call_command("loaddata", "messages", verbosity=0)
        call_command("loaddata", "mailings", verbosity=0)

        self.stdout.write(self.style.NOTICE("▶ Пересчитываем статусы рассылок..."))
        now = timezone.now()
        updated = 0
        for m in Mailing.objects.all():
            # если модель имеет вычисление статуса — синхронизируем
            status_before = m.status
            m.status = m.compute_status()
            m.save(update_fields=["status", "updated_at"])
            updated += int(status_before != m.status)

        self.stdout.write(self.style.SUCCESS(f"✅ Готово. Обновлено статусов: {updated}."))