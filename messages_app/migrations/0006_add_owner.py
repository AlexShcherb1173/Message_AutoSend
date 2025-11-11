from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def fill_owner_messages(apps, schema_editor):
    UserModel = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Message = apps.get_model("messages_app", "Message")

    owner = (
        UserModel.objects.filter(is_superuser=True).order_by("id").first()
        or UserModel.objects.order_by("id").first()
    )
    if owner is None:
        kwargs = {}
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

    Message.objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # ("messages_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="messages_owned",
                verbose_name="Владелец",
                help_text="Пользователь-владелец шаблона сообщения.",
                null=True,
                blank=True,
                db_index=True,
            ),
        ),
        migrations.RunPython(fill_owner_messages, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="message",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="messages_owned",
                verbose_name="Владелец",
                help_text="Пользователь-владелец шаблона сообщения.",
                null=False,
                blank=False,
                db_index=True,
            ),
        ),
    ]
