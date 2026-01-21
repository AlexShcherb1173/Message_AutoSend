from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from mailings.models import Mailing, MailingStatus
from tests.helpers import create_message, create_recipient, create_user


class MailingModelStatusTests(TestCase):
    def setUp(self):
        self.u = create_user()
        self.msg = create_message(self.u)
        self.r = create_recipient(self.u)

    def test_end_after_start_constraint(self):
        start = timezone.now()
        end = start
        m = Mailing(owner=self.u, message=self.msg, start_at=start, end_at=end)
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_compute_status_created_before_window(self):
        start = timezone.now() + timezone.timedelta(hours=1)
        end = start + timezone.timedelta(hours=1)
        m = Mailing.objects.create(owner=self.u, message=self.msg, start_at=start, end_at=end)
        m.recipients.set([self.r])
        self.assertEqual(m.compute_status(), MailingStatus.CREATED)

    def test_compute_status_running_in_window(self):
        start = timezone.now() - timezone.timedelta(minutes=10)
        end = timezone.now() + timezone.timedelta(minutes=10)
        m = Mailing.objects.create(owner=self.u, message=self.msg, start_at=start, end_at=end)
        m.recipients.set([self.r])
        self.assertEqual(m.compute_status(), MailingStatus.RUNNING)

    def test_compute_status_finished_after_end(self):
        start = timezone.now() - timezone.timedelta(days=2)
        end = timezone.now() - timezone.timedelta(days=1)
        m = Mailing.objects.create(owner=self.u, message=self.msg, start_at=start, end_at=end)
        m.recipients.set([self.r])
        self.assertEqual(m.compute_status(), MailingStatus.FINISHED)
