from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0009_fill_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recipient",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                related_name="recipients",
                verbose_name="Владелец",
                help_text="Пользователь-владелец карточки клиента.",
                null=False, blank=False, db_index=True,
            ),
        ),
    ]