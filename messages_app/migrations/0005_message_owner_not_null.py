from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        ("messages_app", "0004_fill_owner"),
    ]
    operations = [
        migrations.AlterField(
            model_name="message",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.deletion.PROTECT,
                related_name="messages_owned",
                verbose_name="Владелец",
                help_text="Пользователь-владелец шаблона сообщения.",
                null=False, blank=False,
            ),
        ),
    ]
