from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from scheduler.models import Event, Reminder

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'Passw0rd!234')

    def test_event_end_before_start_invalid(self):
        start = timezone.now() + timedelta(hours=1)
        end = start - timedelta(minutes=5)
        ev = Event(
            owner=self.user, title='Inválido',
            start=start, end=end, is_all_day=False
        )
        with self.assertRaises(ValidationError):
            ev.clean()

    def test_all_day_normalizes_times(self):
        start = timezone.now().replace(hour=10, minute=30, second=45, microsecond=123456)
        end = start + timedelta(hours=3)
        ev = Event(
            owner=self.user, title='Dia inteiro',
            start=start, end=end, is_all_day=True
        )
        # clean() normaliza
        ev.clean()
        self.assertEqual(ev.start.hour, 0)
        self.assertEqual(ev.start.minute, 0)
        self.assertEqual(ev.start.second, 0)
        self.assertEqual(ev.end.hour, 23)
        self.assertEqual(ev.end.minute, 59)

    def test_reminder_compute_and_save_sets_scheduled_for(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        ev = Event.objects.create(
            owner=self.user, title='Reunião',
            start=start, end=end, is_all_day=False
        )
        r = Reminder.objects.create(event=ev, minutes_before=30)
        expected = ev.start - timedelta(minutes=30)
        self.assertEqual(r.scheduled_for.replace(microsecond=0), expected.replace(microsecond=0))
