from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from scheduler.models import Event, Reminder, NotificationLog
from scheduler.tasks import check_due_reminders


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    DEFAULT_FROM_EMAIL='Agenda <no-reply@agenda.local>',
)
class AgendaE2ETest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='Passw0rd!234',
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_health(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'ok')

    def test_create_event_creates_default_reminder_and_filter_date_and_export_ics(self):
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
        # cria evento
        resp = self.client.post('/api/events/', payload, format='json')
        self.assertEqual(resp.status_code, 201, resp.content)
        event_id = resp.data['id']
        event = Event.objects.get(id=event_id, owner=self.user)

        # lembrete padrão 15 minutos
        reminders = event.reminders.all()
        self.assertEqual(reminders.count(), 1)
        self.assertEqual(reminders.first().minutes_before, 15)

        # filtro por dia
        day = start.date().isoformat()
        resp = self.client.get(f'/api/events/?date={day}')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(item['id'] == event_id for item in resp.data))

        # export ICS
        resp = self.client.get(f'/api/events/{event_id}/export/ics/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/calendar', resp.get('Content-Type', ''))
        self.assertIn('SUMMARY:Reunião de Sprint', resp.content.decode('utf-8'))

    def test_due_reminder_sends_email_and_logs(self):
        # criar evento que começa em 1 minuto
        start = timezone.now() + timedelta(minutes=1)
        end = start + timedelta(minutes=30)
        event = Event.objects.create(
            owner=self.user,
            title='Chamada rápida',
            description='Status call',
            location='Teams',
            start=start,
            end=end,
            is_all_day=False,
        )
        # lembrete que já está vencido (2 min antes de um evento que começa em 1 min)
        reminder = Reminder.objects.create(event=event, minutes_before=2)

        # roda a task de verificação
        result = check_due_reminders()
        self.assertIsInstance(result, dict)
        self.assertIn('sent', result)
        self.assertEqual(result['sent'], 1)  # valida contador de envios ✅

        reminder.refresh_from_db()

        # deve ter sido enviado
        self.assertTrue(reminder.is_sent)
        self.assertIsNotNone(reminder.sent_at)

        # log de notificação
        log_exists = NotificationLog.objects.filter(
            user=self.user, event=event, status=NotificationLog.STATUS_SENT
        ).exists()
        self.assertTrue(log_exists)

        # e-mail enviado (locmem)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Lembrete: Chamada rápida', mail.outbox[0].subject)

    def test_permissions_on_reminder_creation(self):
        # evento de outro usuário
        User = get_user_model()
        bob = User.objects.create_user('bob', 'bob@example.com', 'Passw0rd!234')
        other_event = Event.objects.create(
            owner=bob,
            title='Evento do Bob',
            description='Privado',
            location='Sala A',
            start=timezone.now() + timedelta(hours=1),
            end=timezone.now() + timedelta(hours=2),
            is_all_day=False,
        )

        # tentar criar lembrete no evento do Bob pela API
        payload = {'event': other_event.id, 'minutes_before': 10, 'channel': 'email'}
        resp = self.client.post('/api/reminders/', payload, format='json')
        self.assertEqual(resp.status_code, 403)
