from django.db import migrations


class Migration(migrations.Migration):
    # ВАЖНО: впиши ровно те имена, что у тебя в ошибке (твои "листья")
    dependencies = [
        ("messages_app", "0002_alter_message_body_alter_message_subject_and_more"),
        ("messages_app", "0005_message_owner_not_null"),
        ("messages_app", "0006_add_owner"),
        ("messages_app", "0009_owner_not_null"),
    ]

    operations = []
