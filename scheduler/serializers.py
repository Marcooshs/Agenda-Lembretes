from rest_framework import serializers
from .models import Event, Reminder, NotificationLog


class ReminderInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id', 'minutes_before', 'channel', 'scheduled_for', 'is_sent', 'sent_at']
        read_only_fields = ['scheduled_for', 'is_sent', 'sent_at']


class ReminderSerializer(serializers.ModelSerializer):
    # usado nos endpoints de /api/reminders/ (inclui o campo event)
    class Meta:
        model = Reminder
        fields = ['id', 'event', 'minutes_before', 'channel', 'scheduled_for', 'is_sent', 'sent_at']
        read_only_fields = ['scheduled_for', 'is_sent', 'sent_at']


class EventSerializer(serializers.ModelSerializer):
    # usado nos endpoints de /api/events/ (aninha lembretes sem o campo event para evitar recursão)
    reminders = ReminderInlineSerializer(many=True, required=False)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'location',
            'start', 'end', 'is_all_day', 'reminders',
        ]

    def create(self, validated_data):
        reminders_data = validated_data.pop('reminders', [])
        event = Event.objects.create(owner=self.context['request'].user, **validated_data)
        for r in reminders_data:
            Reminder.objects.create(event=event, **r)
        if not reminders_data:
            Reminder.objects.get_or_create(event=event, minutes_before=15)
        return event

    def update(self, instance, validated_data):
        reminders_data = validated_data.pop('reminders', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if reminders_data is not None:
            instance.reminders.all().delete()
            for r in reminders_data:
                Reminder.objects.create(event=instance, **r)
        return instance


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ['id', 'event', 'reminder', 'user', 'channel', 'status', 'error_message', 'created_at']
        read_only_fields = fields
