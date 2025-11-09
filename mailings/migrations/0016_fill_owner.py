from django.db import migrations
from django.conf import settings

def fill_owner_forward(apps, schema_editor):
    user_app, user_model = settings.AUTH_USER_MODEL.split(".")
    Mailing = apps.get_model("mailings", "Mailing")
    User = apps.get_model(user_app, user_model)

    # 1) пробуем суперпользователя
    owner = User.objects.filter(is_superuser=True).order_by('id').first()
    # 2) иначе любой пользователь
    if owner is None:
        owner = User.objects.order_by('id').first()

    if owner is None:
        # если нет ни одного пользователя — оставим NULL (следующий шаг не делай)
        return

    Mailing.objects.filter(owner__isnull=True).update(owner=owner)

class Migration(migrations.Migration):
    dependencies = [
        ('mailings', '0015_add_owner_nullable'),
    ]
    operations = [
        migrations.RunPython(fill_owner_forward, migrations.RunPython.noop),
    ]