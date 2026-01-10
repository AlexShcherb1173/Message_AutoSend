from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from mailings.models import MailingStatus
from tests.helpers import (create_mailing, create_message, create_recipient, create_user)


class MailingViewsTests(TestCase):
    def setUp(self):
        self.owner = create_user("owner@example.com")
        self.other = create_user("other@example.com")
        self.manager = create_user("manager@example.com", is_staff=True)
        # дадим manager право disable_mailing
        perm = Permission.objects.get(codename="disable_mailing")
        self.manager.user_permissions.add(perm)

        self.msg = create_message(self.owner)
        self.r = create_recipient(self.owner)
        self.m = create_mailing(
            self.owner,
            self.msg,
            [self.r],
            start_at=timezone.now() - timezone.timedelta(minutes=1),
            end_at=timezone.now() + timezone.timedelta(hours=1),
        )

    @patch("mailings.views.send_mailing", autospec=True)
    def test_owner_can_send(self, mocked_send):
        mocked_send.return_value.total = 1
        mocked_send.return_value.sent = 1
        mocked_send.return_value.skipped = 0

        self.client.login(email="owner@example.com", password="pass12345")
        resp = self.client.post(reverse("mailings:send", args=[self.m.pk]), data={})
        self.assertEqual(resp.status_code, 302)

    def test_other_cannot_see_detail(self):
        self.client.login(email="other@example.com", password="pass12345")
        resp = self.client.get(reverse("mailings:detail", args=[self.m.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_manager_can_disable(self):
        self.client.login(email="manager@example.com", password="pass12345")
        resp = self.client.post(reverse("mailings:disable", args=[self.m.pk]))
        self.assertEqual(resp.status_code, 302)
        self.m.refresh_from_db()
        self.assertEqual(self.m.status, MailingStatus.FINISHED)
