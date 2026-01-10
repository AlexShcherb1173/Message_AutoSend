from django.test import TestCase
from django.urls import reverse

from tests.helpers import create_user, create_recipient


class RecipientViewsPermissionsTests(TestCase):
    def setUp(self):
        self.u1 = create_user("u1@example.com")
        self.u2 = create_user("u2@example.com")
        self.r1 = create_recipient(self.u1, email="r1@example.com", full_name="U1 Rec")
        self.r2 = create_recipient(self.u2, email="r2@example.com", full_name="U2 Rec")

    def test_list_requires_login(self):
        resp = self.client.get(reverse("clients:recipient_list"))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_list_shows_only_own(self):
        self.client.login(email="u1@example.com", password="pass12345")
        resp = self.client.get(reverse("clients:recipient_list"))
        self.assertContains(resp, "r1@example.com")
        self.assertNotContains(resp, "r2@example.com")

    def test_detail_forbidden_for_other_owner(self):
        self.client.login(email="u1@example.com", password="pass12345")
        resp = self.client.get(reverse("clients:recipient_detail", args=[self.r2.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_create_sets_owner(self):
        self.client.login(email="u1@example.com", password="pass12345")
        resp = self.client.post(reverse("clients:recipient_create"), data={
            "email": "new@example.com",
            "full_name": "Новый Получатель",
            "comment": "ok",
        })
        self.assertEqual(resp.status_code, 302)
        # owner должен быть u1
        from clients.models import Recipient
        obj = Recipient.objects.get(email="new@example.com")
        self.assertEqual(obj.owner_id, self.u1.id)