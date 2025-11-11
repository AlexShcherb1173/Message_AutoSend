from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("messages_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                related_name="messages_owned",
                verbose_name="Владелец",
                help_text="Пользователь-владелец шаблона сообщения.",
                null=True,
                blank=True,
                db_index=True,
            ),
        ),
    ]
