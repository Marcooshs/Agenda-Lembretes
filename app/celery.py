import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

celery_app = Celery("app")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

# Alinhar timezone com o Django
celery_app.conf.timezone = settings.TIME_ZONE
celery_app.conf.enable_utc = False

# Agenda do Beat: roda a cada 60s
celery_app.conf.beat_schedule = {
    "check-due-reminders-every-minute": {
        "task": "scheduler.check_due_reminders",
        "schedule": 60.0,
    },
}

# Alias opcional (útil para alguns CLIs): `celery -A app.celery ...`
app = celery_app
