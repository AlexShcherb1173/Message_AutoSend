from django.db import migrations

class Migration(migrations.Migration):
    # ВАЖНО: впиши ровно те имена, что у тебя в ошибке (твои "листья")
    dependencies = [
        ('clients', '0003_alter_recipient_options_alter_recipient_comment_and_more'),
        ('clients', '0006_recipient_owner_not_null'),
        ('clients', '0007_add_owner'),
        ('clients', '0010_owner_not_null'),
    ]

    operations = []