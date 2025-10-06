from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Reminder, NotificationLog

def send_event_email(user_email: str, subject: str, message: str) -> None:
    send_mail(
        subject= subject,
        message= message,
        from_email= settings.DEFAULT_FROM_EMAIL,
        recipient_list= [user_email],
        fail_silently= False,
    )

def notify_reminder(reminder: Reminder):
    event = reminder.event
    user = event.owner
    subject = f'Lembrete: {event.title}'
    start_fmt = timezone.localtime(event.start).strftime("%d/%m/%Y %H:%M")
    body = (
        f'Olá {user.get_username()},\n\n'
        f'Seu evento "{event.title}" começa em {reminder.minutes_before} minutos.\n'
        f'Início: {start_fmt}\n'
        f'Local: {event.location or '-'}\n\n'
        f'Descrição:\n{event.description or '-'}\n'
    )
    try:
        send_event_email(user.email, subject, body)
        NotificationLog.objects.create(
            event= event,
            reminder= reminder,
            user= user,
            channel= reminder.channel,
            status= NotificationLog.STATUS_SENT,
        )
        reminder.is_sent = True
        reminder.sent_at = timezone.now()
        reminder.save(update_fields=['is_sent', 'sent_at'])
        return True, ""
    except Exception as exc:
        NotificationLog.objects.create(
            event= event,
            reminder= reminder,
            user= user,
            channel= reminder.channel,
            status= NotificationLog.STATUS_FAILED,
            error_message=str(exc),
        )
        return False, str(exc)
