from django.test import TestCase

from messages_app.forms import MessageForm


class MessageFormTests(TestCase):
    def test_subject_min_3(self):
        form = MessageForm(data={"subject": "  a ", "body": "x"})
        self.assertFalse(form.is_valid())
        self.assertIn("subject", form.errors)

    def test_valid(self):
        form = MessageForm(data={"subject": "Привет", "body": "Текст"})
        self.assertTrue(form.is_valid())
