from django.db import migrations

class Migration(migrations.Migration):
    # ВАЖНО: впиши ровно те имена, что у тебя в ошибке (твои "листья")
    dependencies = [
        ('mailings', '0005_mailingattempt_triggered_by_and_more'),
        ('mailings', '0008_mailing_owner_not_null'),
        ('mailings', '0009_add_owner_to_mailing'),
        ('mailings', '0010_add_owner'),
        ('mailings', '0013_owner_not_null'),
    ]

    operations = []