from django.db import migrations


def get_or_create_system_user(apps):
    User = (
        apps.get_model("users", "User")
        if apps.is_installed("users")
        else apps.get_model("auth", "User")
    )
    su = User.objects.filter(is_superuser=True).order_by("id").first()
    if su:
        return su
    sys_user, _ = User.objects.get_or_create(
        email="system@local",
        defaults={
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
            "username": "system@local" if hasattr(User, "username") else "system",
        },
    )
    if hasattr(sys_user, "set_unusable_password"):
        sys_user.set_unusable_password()
        sys_user.save(update_fields=["password"])
    return sys_user


def fill_owner(apps, schema_editor):
    Mailing = apps.get_model("mailings", "Mailing")
    Message = apps.get_model("messages_app", "Message")
    owner = get_or_create_system_user(apps)

    # Попытаемся унаследовать владельца от связанного сообщения, иначе system
    for m in Mailing.objects.filter(owner__isnull=True).select_related("message"):
        msg_owner_id = None
        if m.message_id:
            msg = Message.objects.filter(id=m.message_id).only("owner_id").first()
            msg_owner_id = getattr(msg, "owner_id", None)
        m.owner_id = msg_owner_id or owner.id
        m.save(update_fields=["owner"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("mailings", "0006_mailing_owner_nullable"),
        ("messages_app", "0004_fill_owner"),
    ]
    operations = [
        migrations.RunPython(fill_owner, reverse_code=noop),
    ]
