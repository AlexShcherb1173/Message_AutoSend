from django.db import migrations
from django.conf import settings


def fill_owner(apps, schema_editor):
    user_app, user_model = settings.AUTH_USER_MODEL.split(".")
    Mailing = apps.get_model("mailings", "Mailing")
    User = apps.get_model(user_app, user_model)

    owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if owner is None:
        owner = User.objects.create(
            username="system", is_staff=False, is_superuser=False
        )
        try:
            owner.set_unusable_password()
            owner.save(update_fields=["password"])
        except Exception:
            pass

    Mailing.objects.filter(owner__isnull=True).update(owner=owner)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("mailings", "0011_add_owner_nullable"),
    ]

    operations = [migrations.RunPython(fill_owner, noop)]
