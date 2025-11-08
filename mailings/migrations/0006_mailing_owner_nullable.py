from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        ("mailings", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name="mailing",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.deletion.PROTECT,
                related_name="mailings",
                verbose_name="Владелец",
                help_text="Пользователь-владелец этой рассылки.",
                null=True, blank=True,
            ),
        ),
    ]