from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def fill_owner_mailings(apps, schema_editor):
    UserModel = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Mailing = apps.get_model("mailings", "Mailing")

    owner = (
        UserModel.objects.filter(is_superuser=True).order_by("id").first()
        or UserModel.objects.order_by("id").first()
    )

    if owner is None:
        # создаём техпользователя с минимально возможными полями
        kwargs = {}
        # Поддержка username/email в зависимости от кастомной модели
        if hasattr(UserModel, "username"):
            kwargs["username"] = "system"
        if hasattr(UserModel, "email"):
            kwargs.setdefault("email", "system@local")

        owner = UserModel.objects.create(is_active=False, **kwargs)
        try:
            owner.set_unusable_password()
            owner.save(update_fields=[])
        except Exception:
            pass

    Mailing.objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # Поставь тут последнюю имеющуюся миграцию твоего app `mailings`, например:
        # ("mailings", "0001_initial"),
    ]

    operations = [
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
        migrations.RunPython(fill_owner_mailings, migrations.RunPython.noop),
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
