from django.test import TestCase

from clients.forms import RecipientForm


class RecipientFormTests(TestCase):
    def test_full_name_clean_min_3(self):
        form = RecipientForm(
            data={"email": "a@b.com", "full_name": "Аа", "comment": ""}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)

    def test_valid(self):
        form = RecipientForm(
            data={"email": "a@b.com", "full_name": "Алиса", "comment": ""}
        )
        self.assertTrue(form.is_valid())
