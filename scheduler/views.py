from rest_framework import viewsets, permissions, decorators
from rest_framework.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from .models import Event, Reminder, NotificationLog
from .serializers import EventSerializer, ReminderSerializer, NotificationLogSerializer
from .permissions import IsOwner
from .filters import EventFilter

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start', 'end', 'title']

    def get_queryset(self):
        return Event.objects.filter(owner= self.request.user).prefetch_related('reminders')

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied('Sem permissão.')
        instance.delete()

    @decorators.action(detail= True, methods=['get'], url_path= 'export/ics')
    def export_ics(self, request, pk=None):
        event = self.get_object()
        start = timezone.localtime(event.start).strftime("%Y%m%dT%H%M%S")
        end = timezone.localtime(event.end).strftime("%Y%m%dT%H%M%S")
        description = (event.description or "").replace("\n", " ")
        location = event.location or ""
        ics = "".join(
            [
                "BEGIN:VCALENDAR\r\n",
                "VERSION:2.0\r\n",
                "PRODID:-//Agenda//PT-BR//EN\r\n",
                "CALSCALE:GREGORIAN\r\n",
                "METHOD:PUBLISH\r\n",
                "BEGIN:VEVENT\r\n",
                f"UID:event-{event.id}@agenda\r\n",
                f"DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%S')}\r\n",
                f"DTSTART:{start}\r\n",
                f"DTEND:{end}\r\n",
                f"SUMMARY:{event.title}\r\n",
                f"DESCRIPTION:{description}\r\n",
                f"LOCATION:{location}\r\n",
                "END:VEVENT\r\n",
                "END:VCALENDAR\r\n",
            ]
        )
        resp = HttpResponse(ics, content_type='text/calendar; charset=utf-8')
        resp["Content-Disposition"] = f'attachment; filename="event-{event.id}.ics"'
        return resp

class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    ordering_fields = ["scheduled_for", "minutes_before"]

    def get_queryset(self):
        # Lembretes apenas de eventos do usuário
        return Reminder.objects.select_related('event', 'event__owner').filter(event__owner= self.request.user)

    def perform_create(self, serializer):
        event = serializer.validated_data.get("event")
        if event.owner != self.request.user:
            raise PermissionDenied('Sem permissão para adicionar lembrete a este evento.')
        serializer.save()

class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['created_at']

    def get_queryset(self):
        return NotificationLog.objects.filter(user= self.request.user).select_related('event', 'reminder')