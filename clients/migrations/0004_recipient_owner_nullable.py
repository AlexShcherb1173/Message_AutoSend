from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="recipient",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.deletion.PROTECT,
                related_name="recipients",
                verbose_name="Владелец",
                help_text="Пользователь-владелец карточки клиента.",
                null=True,  # временно допускаем NULL
                blank=True,
            ),
        ),
    ]
