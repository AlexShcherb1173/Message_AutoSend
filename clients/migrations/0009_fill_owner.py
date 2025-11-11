from django.conf import settings
from django.db import migrations


def fill_owner(apps, schema_editor):
    """
    Заполнить поле owner у существующих клиентов.
    Берём первого суперпользователя, иначе первого попавшегося пользователя.
    """
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app_label, user_model_name)
    Recipient = apps.get_model("clients", "Recipient")

    owner = User.objects.filter(is_superuser=True).order_by("id").first()
    if owner is None:
        owner = User.objects.order_by("id").first()

    if owner is None:
        # В системе ещё нет пользователей — просто оставим NULL.
        # Позже, перед миграцией "owner_not_null", нужно будет создать пользователя
        # и руками обновить NULL-ы, либо пропустить "not null" до появления юзеров.
        return

    Recipient.objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0008_add_owner_nullable"),
        # Гарантируем, что таблица кастомного пользователя уже есть:
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(fill_owner, migrations.RunPython.noop),
    ]
