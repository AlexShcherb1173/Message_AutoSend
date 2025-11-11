from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [("mailings", "0012_fill_owner")]

    operations = [
        migrations.AlterField(
            model_name="mailing",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                related_name="mailings",
                verbose_name="Владелец",
                help_text="Пользователь-владелец этой рассылки.",
                null=False,
                blank=False,
                db_index=True,
            ),
        ),
    ]
