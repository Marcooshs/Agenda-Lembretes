from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APIClient
from scheduler.models import Event

User = get_user_model()

class ApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'Passw0rd!234')
        self.client = APIClient()
        # autentica sem depender de token/JWT
        self.client.force_authenticate(user=self.user)

    def test_create_event_creates_default_reminder_and_export_ics(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        payload = {
            'title': 'Reunião de Sprint',
            'description': 'Alinhar entregas',
            'location': 'Google Meet',
            'start': start.isoformat(),
            'end': end.isoformat(),
            'is_all_day': False,
        }
        # cria
        resp = self.client.post('/api/events/', payload, format='json')
        self.assertEqual(resp.status_code, 201, resp.content)
        event_id = resp.data['id']
        ev = Event.objects.get(id=event_id, owner=self.user)

        # lembrete padrão (15 min) — seu viewset/serializer deve criar
        self.assertEqual(ev.reminders.count(), 1)
        self.assertEqual(ev.reminders.first().minutes_before, 15)

        # export ICS
        resp = self.client.get(f'/api/events/{event_id}/export/ics/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/calendar', resp.get('Content-Type', ''))
        self.assertIn('SUMMARY:Reunião de Sprint', resp.content.decode('utf-8'))

    def test_permissions_on_reminder_creation(self):
        bob = User.objects.create_user('bob', 'bob@example.com', 'Passw0rd!234')
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        other = Event.objects.create(
            owner=bob, title='Privado', description='X',
            location='Sala A', start=start, end=end, is_all_day=False
        )
        payload = {'event': other.id, 'minutes_before': 10, 'channel': 'email'}
        resp = self.client.post('/api/reminders/', payload, format='json')
        self.assertEqual(resp.status_code, 403)
