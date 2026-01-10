from django.test import TestCase
from django.urls import reverse

from tests.helpers import create_message, create_user


class MessageViewsPermissionsTests(TestCase):
    def setUp(self):
        self.u1 = create_user("u1@example.com")
        self.u2 = create_user("u2@example.com")
        self.m1 = create_message(self.u1, subject="S1", body="B1")
        self.m2 = create_message(self.u2, subject="S2", body="B2")

    def test_list_only_own(self):
        self.client.login(email="u1@example.com", password="pass12345")
        resp = self.client.get(reverse("messages_app:message_list"))
        self.assertContains(resp, "S1")
        self.assertNotContains(resp, "S2")

    def test_detail_other_owner_404(self):
        self.client.login(email="u1@example.com", password="pass12345")
        resp = self.client.get(
            reverse("messages_app:message_detail", args=[self.m2.pk])
        )
        self.assertEqual(resp.status_code, 404)
