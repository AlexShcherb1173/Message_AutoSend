from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone

from tests.helpers import create_user, create_message, create_recipient, create_mailing
from mailings.tasks import run_due_mailings
from mailings.models import MailingStatus


class RunDueMailingsTests(TestCase):
    def setUp(self):
        self.u = create_user()
        self.msg = create_message(self.u)
        self.r = create_recipient(self.u)
        self.m = create_mailing(
            self.u, self.msg, [self.r],
            start_at=timezone.now() - timezone.timedelta(minutes=1),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            last_sent_at=None
        )

    @patch("mailings.tasks.send_mailing", autospec=True)
    def test_run_due_mailings_processes(self, mocked_send):
        n = run_due_mailings(triggered_by="test")
        self.assertEqual(n, 1)
        self.m.refresh_from_db()
        self.assertIn(self.m.status, [MailingStatus.RUNNING, MailingStatus.CREATED])

    @patch("mailings.tasks._acquire_lock", autospec=True, return_value=False)
    def test_lock_prevents_parallel_run(self, mocked_lock):
        n = run_due_mailings(triggered_by="test")
        self.assertEqual(n, 0)