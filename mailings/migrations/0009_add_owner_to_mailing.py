from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def set_owner_for_existing_mailings(apps, schema_editor):
    """
    Заполняем owner для уже имеющихся рассылок:
      1) сначала берём первого суперпользователя,
      2) если нет — первого обычного пользователя,
      3) если в системе вообще нет пользователей — создаём технического.
    """
    User = apps.get_model(settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1])
    Mailing = apps.get_model("mailings", "Mailing")

    # Пытаемся найти подходящего владельца
    owner = None
    try:
        owner = User.objects.filter(is_superuser=True).order_by("id").first()
        if owner is None:
            owner = User.objects.order_by("id").first()
    except Exception:
        owner = None

    # Если пользователей нет — создаём технического
    if owner is None:
        # Важно: у кастомной модели пользователя могут быть другие обязательные поля.
        # Используем минимальный набор и set_unusable_password().
        owner = User.objects.create(
            **{
                (hasattr(User, "username") and "username" or "email"): "system@local",
                "is_active": False,
            }
        )
        try:
            owner.set_unusable_password()
            owner.save(update_fields=[])
        except Exception:
            pass

    # Проставляем owner всем рассылкам, где он пуст
    Mailing.objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        ("mailings", "0001_initial"),  # <-- поменяй на последнюю актуальную миграцию в mailings
        ("users", "0001_initial"),     # <-- при необходимости поправь имя приложения/миграции с User
    ]

    operations = [
        # 1) добавляем поле как nullable
        migrations.AddField(
            model_name="mailing",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="mailings",
                verbose_name="Владелец",
                help_text="Пользователь-владелец этой рассылки.",
                null=True,
                blank=True,
                db_index=True,
            ),
        ),
        # 2) заполняем owner для уже существующих строк
        migrations.RunPython(set_owner_for_existing_mailings, migrations.RunPython.noop),
        # 3) делаем поле обязательным
        migrations.AlterField(
            model_name="mailing",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="mailings",
                verbose_name="Владелец",
                help_text="Пользователь-владелец этой рассылки.",
                null=False,
                blank=False,
                db_index=True,
            ),
        ),
    ]