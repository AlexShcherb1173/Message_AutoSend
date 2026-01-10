from django.contrib.auth import get_user_model
from django.utils import timezone


def create_user(email="u1@example.com", password="pass12345", **kwargs):
    User = get_user_model()
    return User.objects.create_user(email=email, password=password, **kwargs)


def create_superuser(email="admin@example.com", password="pass12345", **kwargs):
    User = get_user_model()
    return User.objects.create_superuser(email=email, password=password, **kwargs)


def create_recipient(
    owner, email="r1@example.com", full_name="Иван Петров", comment=""
):
    from clients.models import Recipient

    return Recipient.objects.create(
        owner=owner, email=email, full_name=full_name, comment=comment
    )


def create_message(owner, subject="Тема", body="Текст"):
    from messages_app.models import Message

    return Message.objects.create(owner=owner, subject=subject, body=body)


def create_mailing(
    owner, message, recipients, start_at=None, end_at=None, last_sent_at=None
):
    from mailings.models import Mailing, MailingStatus

    start_at = start_at or timezone.now() + timezone.timedelta(minutes=1)
    end_at = end_at or timezone.now() + timezone.timedelta(days=1)

    mailing = Mailing.objects.create(
        owner=owner,
        message=message,
        start_at=start_at,
        end_at=end_at,
        last_sent_at=last_sent_at,
        status=MailingStatus.CREATED,
    )
    mailing.recipients.set(recipients)
    mailing.refresh_status(save=True)
    return mailing
