from django.test import TestCase
from clients.models import Recipient


class RecipientModelTests(TestCase):
    """Набор тестов для модели Recipient.
    Проверяет корректность поведения методов модели получателя,
    включая строковое представление (__str__) и возможные поля."""

    def test_recipient_str(self):
        """Проверяет метод __str__ модели Recipient.
        Убеждается, что при создании получателя строковое представление
        возвращается в формате:
            "Ф. И. О. <email>"
        Пример:
            Иван Петров <u@example.com>"""
        r = Recipient.objects.create(email="u@example.com", full_name="Иван Петров")
        self.assertEqual(str(r), "Иван Петров <u@example.com>")
