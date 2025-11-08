from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from mailings.models import Mailing
from messages_app.models import Message
from clients.models import Recipient
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    """
    Создаёт/обновляет группу «Менеджеры» и назначает права:
      • Просмотр всех рассылок/получателей/сообщений.
      • Отключение рассылок.
      • Просмотр списка пользователей (и право их блокировать через админку:
        это обычное 'change_user', чтобы менять is_active).
    """
    help = "Создать группу «Менеджеры» и выдать ей необходимые права."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="Менеджеры")

        perms_codes = []

        # Кастомные perms (из Meta.permissions)
        mail_ct = ContentType.objects.get_for_model(Mailing)
        msg_ct = ContentType.objects.get_for_model(Message)
        rec_ct = ContentType.objects.get_for_model(Recipient)

        perms_codes += [
            ("mailings", "view_all_mailings"),
            ("mailings", "disable_mailing"),
            ("messages_app", "view_all_messages"),
            ("clients", "view_all_recipients"),
        ]

        # Базовые 'view_*' чтобы видеть объекты в админке
        base_codes = [
            ("mailings", "view_mailing"),
            ("mailings", "view_mailinglog"),
            ("mailings", "view_mailingattempt"),
            ("messages_app", "view_message"),
            ("clients", "view_recipient"),
        ]
        perms_codes += base_codes

        # Права на пользователей — смотреть и изменять (для блокировки is_active)
        User = get_user_model()
        user_ct = ContentType.objects.get_for_model(User)
        user_perm_codes = [("auth", "view_user"), ("auth", "change_user")]
        # в кастомной модели пользователя app_label может быть 'users'
        # Добавим безопасно реальные коды:
        for codename in ("view_user", "change_user"):
            try:
                p = Permission.objects.get(content_type=user_ct, codename=codename)
                group.permissions.add(p)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Permission {codename} for user model not found"))

        # Назначаем кастомные + базовые perms по content_type
        mapping = {
            "mailings": mail_ct,
            "messages_app": msg_ct,
            "clients": rec_ct,
        }
        for app_label, codename in perms_codes:
            ct = mapping.get(app_label)
            if ct is None:
                # для auth.* уже обработали выше
                continue
            try:
                p = Permission.objects.get(content_type=ct, codename=codename)
                group.permissions.add(p)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Permission {app_label}.{codename} not found"))

        self.stdout.write(self.style.SUCCESS("Группа «Менеджеры» обновлена."))