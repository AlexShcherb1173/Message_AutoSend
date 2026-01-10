from django.core.exceptions import ValidationError
from django.test import TestCase

from tests.helpers import create_user
from clients.models import Recipient


class RecipientModelTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_recipient_str_full_name(self):
        r = Recipient.objects.create(owner=self.user, email="u@example.com", full_name="Иван Петров")
        self.assertEqual(str(r), "Иван Петров <u@example.com>")

    def test_email_normalized_on_clean(self):
        r = Recipient(owner=self.user, email="UPPER@EXAMPLE.COM", full_name=" Иван ")
        r.full_clean()
        r.save()
        self.assertEqual(r.email, "upper@example.com")
        self.assertEqual(r.full_name, "Иван")

    def test_full_name_min_length_validator(self):
        r = Recipient(owner=self.user, email="a@b.com", full_name="A")
        with self.assertRaises(ValidationError):
            r.full_clean()

    def test_unique_email(self):
        Recipient.objects.create(owner=self.user, email="dup@example.com", full_name="A A")
        r2 = Recipient(owner=self.user, email="dup@example.com", full_name="B B")
        with self.assertRaises(ValidationError):
            r2.full_clean()