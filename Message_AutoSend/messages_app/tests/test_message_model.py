from django.test import TestCase
from messages_app.models import Message


class TestMessageModel(TestCase):
    def test_str_returns_subject(self):
        m = Message.objects.create(subject="Привет", body="Текст")
        self.assertEqual(str(m), "Привет")