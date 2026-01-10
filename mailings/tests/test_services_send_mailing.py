from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone

from tests.helpers import create_user, create_message, create_recipient, create_mailing
from mailings.models import MailingLog, MailingAttempt, AttemptStatus
from mailings.services import send_mailing


class SendMailingServiceTests(TestCase):
    def setUp(self):
        self.u = create_user()
        self.msg = create_message(self.u, subject="Subj", body="Body")
        self.r1 = create_recipient(self.u, email="a@a.com")
        self.r2 = create_recipient(self.u, email="b@b.com")
        self.m = create_mailing(self.u, self.msg, [self.r1, self.r2],
                                start_at=timezone.now() - timezone.timedelta(minutes=1),
                                end_at=timezone.now() + timezone.timedelta(hours=1))

    def test_dry_run_creates_logs_and_success_attempt(self):
        result = send_mailing(self.m, user=self.u, dry_run=True)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.sent, 0)
        self.assertEqual(result.skipped, 2)

        self.assertEqual(MailingLog.objects.filter(mailing=self.m, status="DRY_RUN").count(), 2)
        attempt = MailingAttempt.objects.filter(mailing=self.m).first()
        self.assertEqual(attempt.status, AttemptStatus.SUCCESS)

    @patch("mailings.services.send_mail", autospec=True, return_value=1)
    def test_real_send_success(self, mocked_send_mail):
        result = send_mailing(self.m, user=self.u, dry_run=False)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.sent, 2)
        self.assertEqual(MailingLog.objects.filter(mailing=self.m, status="SENT").count(), 2)
        self.m.refresh_from_db()
        self.assertIsNotNone(self.m.last_sent_at)

    @patch("mailings.services.send_mail", autospec=True, side_effect=Exception("smtp down"))
    def test_real_send_errors_are_logged(self, mocked_send_mail):
        result = send_mailing(self.m, user=self.u, dry_run=False)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.sent, 0)
        self.assertEqual(MailingLog.objects.filter(mailing=self.m, status="ERROR").count(), 2)