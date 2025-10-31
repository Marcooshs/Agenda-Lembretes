from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import Reminder
from .services import notify_reminder


@shared_task(name='scheduler.check_due_reminders')
def check_due_reminders():
    now = timezone.now()
    # Buscar lembretes vencidos e não enviados
    qs = (
        Reminder.objects
        .select_related('event', 'event__owner')
        .filter(is_sent=False, scheduled_for__lte=now)
        .order_by('scheduled_for')
    )
    sent_count = 0
    for reminder in qs:
        # Em transação reduzimos riscos de concorrência
        with transaction.atomic():
            r = Reminder.objects.select_for_update().get(pk=reminder.pk)
            if r.is_sent:
                continue
            ok, _ = notify_reminder(r)
            if ok:
                sent_count += 1
    return {'sent': sent_count}