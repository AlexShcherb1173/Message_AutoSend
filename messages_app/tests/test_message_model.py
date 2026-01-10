from django.test import TestCase

from messages_app.models import Message
from tests.helpers import create_user


class TestMessageModel(TestCase):
    def test_str_returns_subject(self):
        u = create_user("x@x.com")
        m = Message.objects.create(owner=u, subject="Привет", body="Текст")
        self.assertEqual(str(m), "Привет")