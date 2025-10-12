from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

User = settings.AUTH_USER_MODEL


class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start']
        indexes = [
            models.Index(fields=['owner', 'start']),
            models.Index(fields=['start', 'end']),
        ]
        constraints = [
            models.CheckConstraint(check=Q(end__gte=F('start')), name='event_end_gte_start'),
        ]

    def clean(self):
        if self.end < self.start:
            raise ValidationError('Fim do evento não pode ser anterior ao início.')
        if self.is_all_day:
            # normaliza sempre para o dia inteiro quando is_all_day=True
            self.start = self.start.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end = self.end.replace(hour=23, minute=59, second=59, microsecond=0)

    def save(self, *args, **kwargs):
        # Normaliza antes de validar/salvar para garantir consistência
        if self.is_all_day and self.start and self.end:
            self.start = self.start.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end = self.end.replace(hour=23, minute=59, second=59, microsecond=0)
        # Validação de modelo (inclui clean() e validações de campo)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.title} ({self.start:%Y-%m-%d %H:%M})'


class Reminder(models.Model):
    CHANNEL_EMAIL = 'email'
    CHANNEL_CHOICES = [(CHANNEL_EMAIL, 'E-mail')]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    minutes_before = models.PositiveIntegerField(default=15)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=CHANNEL_EMAIL)
    scheduled_for = models.DateTimeField(editable=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['scheduled_for']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'minutes_before', 'channel'],
                name='uniq_reminder_event_minutes_channel',
            ),
        ]
        indexes = [
            models.Index(fields=['is_sent', 'scheduled_for']),
        ]

    def compute_scheduled_for(self):
        return self.event.start - timedelta(minutes=self.minutes_before)

    def clean(self):
        if not self.event or self.event.start is None:
            raise ValidationError('Evento inválido para criar lembrete.')
        self.scheduled_for = self.compute_scheduled_for()

    def save(self, *args, **kwargs):
        # Mantém scheduled_for sempre coerente
        self.scheduled_for = self.compute_scheduled_for()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'Lembrete {self.minutes_before}m antes de "{self.event.title}"'


class NotificationLog(models.Model):
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_SENT, 'Enviado'), (STATUS_FAILED, 'Falhou')]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications')
    reminder = models.ForeignKey(
        Reminder, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=20, default=Reminder.CHANNEL_EMAIL)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at'])]

    def __str__(self) -> str:
        return f'{self.status} - {self.channel} - {self.event.title} - {self.created_at:%Y-%m-%d %H:%M}'
