from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class SignupActivationTests(TestCase):
    def test_signup_creates_inactive_user_and_sends_email(self):
        resp = self.client.post(
            reverse("users:signup"),
            data={
                "email": "new@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "phone": "",
                "country": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        u = User.objects.get(email="new@example.com")
        self.assertFalse(u.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Подтверждение регистрации", mail.outbox[0].subject)

    def test_activate_makes_user_active(self):
        u = User.objects.create_user(email="a@a.com", password="pass12345", is_active=False)
        uidb64 = urlsafe_base64_encode(force_bytes(u.pk))
        resp = self.client.get(reverse("users:activate", kwargs={"uidb64": uidb64, "token": "x"}))
        self.assertEqual(resp.status_code, 302)
        u.refresh_from_db()
        self.assertTrue(u.is_active)
