from django.db import migrations

def get_or_create_system_user(apps):
    User = apps.get_model(*apps.get_app_config('users').models_module.__name__.split('.')[:1], 'User') \
        if apps.is_installed('users') else apps.get_model('auth', 'User')
    # Попробуем взять суперпользователя
    su = User.objects.filter(is_superuser=True).order_by('id').first()
    if su:
        return su
    # Иначе — создаём технического пользователя
    sys_user, _ = User.objects.get_or_create(
        email="system@local",
        defaults={
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,  # удобнее для админ-доступа
            "username": "system@local" if hasattr(User, "username") else "system",
        },
    )
    if hasattr(sys_user, "set_unusable_password"):
        sys_user.set_unusable_password()
        sys_user.save(update_fields=["password"])
    return sys_user

def fill_owner(apps, schema_editor):
    Recipient = apps.get_model("clients", "Recipient")
    owner = get_or_create_system_user(apps)
    Recipient.objects.filter(owner__isnull=True).update(owner=owner)

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0004_recipient_owner_nullable"),
    ]
    operations = [
        migrations.RunPython(fill_owner, reverse_code=noop),
    ]