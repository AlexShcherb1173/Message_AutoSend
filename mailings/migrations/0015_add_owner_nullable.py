from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('mailings', '0014_merge_manual'),  # ← наш merge
    ]

    operations = [
        migrations.AddField(
            model_name='mailing',
            name='owner',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                related_name='mailings',
                verbose_name='Владелец',
                null=True, blank=True,
                help_text='Пользователь-владелец этой рассылки.',
            ),
        ),
        migrations.AddIndex(
            model_name='mailing',
            index=models.Index(fields=['owner'], name='idx_mailing_owner'),
        ),
    ]