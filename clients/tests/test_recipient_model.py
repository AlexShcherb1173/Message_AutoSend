from django.test import TestCase
from clients.models import Recipient

class RecipientModelTests(TestCase):
    def test_recipient_str(self):
        r = Recipient.objects.create(email="u@example.com", full_name="Иван Петров")
        self.assertEqual(str(r), "Иван Петров <u@example.com>")