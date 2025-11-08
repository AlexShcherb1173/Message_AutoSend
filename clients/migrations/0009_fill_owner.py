from django.db import migrations

def fill_owner(apps, schema_editor):
    Recipient = apps.get_model("clients", "Recipient")
    User = apps.get_model(*apps.get_app_config('auth').models_module.__name__.split('.')[:1],)
    # Надёжнее так:
    User = apps.get_model("auth", "User")  # если у вас кастомный User — поменяйте на своё app_label/model

    owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if owner is None:
        # создаём системного пользователя (для кастомной модели может понадобиться скорректировать поля)
        owner = User.objects.create(username="system", is_staff=False, is_superuser=False)
        try:
            owner.set_unusable_password()
            owner.save(update_fields=["password"])
        except Exception:
            pass

    Recipient.objects.filter(owner__isnull=True).update(owner=owner)

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0008_add_owner_nullable"),
    ]

    operations = [
        migrations.RunPython(fill_owner, noop),
    ]