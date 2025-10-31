from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail

from scheduler.models import Event, Reminder, NotificationLog
from scheduler.tasks import check_due_reminders

User = get_user_model()

@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    DEFAULT_FROM_EMAIL='Agenda <no-reply@agenda.local>',
)
class TaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'Passw0rd!234')

    def test_due_reminder_sends_email_and_logs_and_counts(self):
        start = timezone.now() + timedelta(minutes=1)
        end = start + timedelta(minutes=30)
        ev = Event.objects.create(
            owner=self.user, title='Chamada rápida',
            description='Status call', location='Teams',
            start=start, end=end, is_all_day=False
        )
        # lembrete vencido (2 min antes de um evento que começa em 1 min)
        r = Reminder.objects.create(event=ev, minutes_before=2)

        result = check_due_reminders()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('sent'), 1)  # garante contagem

        r.refresh_from_db()
        self.assertTrue(r.is_sent)
        self.assertIsNotNone(r.sent_at)

        self.assertTrue(NotificationLog.objects.filter(
            user=self.user, event=ev, status=NotificationLog.STATUS_SENT
        ).exists())

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Lembrete: Chamada rápida', mail.outbox[0].subject)
