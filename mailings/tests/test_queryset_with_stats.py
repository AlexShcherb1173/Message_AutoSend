from django.test import TestCase
from django.utils import timezone

from tests.helpers import create_user, create_message, create_recipient
from mailings.models import Mailing, MailingLog, MailingAttempt, AttemptStatus


class MailingWithStatsTests(TestCase):
    def setUp(self):
        self.u = create_user()
        self.msg = create_message(self.u)
        self.r1 = create_recipient(self.u, email="a@a.com")
        self.r2 = create_recipient(self.u, email="b@b.com")

        self.m = Mailing.objects.create(
            owner=self.u,
            message=self.msg,
            start_at=timezone.now() - timezone.timedelta(minutes=1),
            end_at=timezone.now() + timezone.timedelta(days=1),
        )
        self.m.recipients.set([self.r1, self.r2])

        MailingLog.objects.create(mailing=self.m, recipient="a@a.com", status="SENT")
        MailingLog.objects.create(mailing=self.m, recipient="b@b.com", status="ERROR")
        MailingAttempt.objects.create(mailing=self.m, status=AttemptStatus.SUCCESS)
        MailingAttempt.objects.create(mailing=self.m, status=AttemptStatus.FAIL)

    def test_with_stats_annotations(self):
        m = Mailing.objects.with_stats().get(pk=self.m.pk)
        self.assertEqual(m.stat_sent_messages, 1)
        self.assertEqual(m.stat_failed_messages, 1)
        self.assertEqual(m.stat_attempt_success, 1)
        self.assertEqual(m.stat_attempt_fail, 1)