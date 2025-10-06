from django.contrib import admin
from .models import Event, Reminder, NotificationLog


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'start', 'end', 'is_all_day')
    list_filter = ('is_all_day',)
    search_fields = ('title', 'description', 'location')
    autocomplete_fields = ('owner',)

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('event', 'minutes_before', 'channel', 'scheduled_for', 'is_sent', 'sent_at')
    list_filter = ('channel', 'is_sent')
    search_fields = ('event__title',)

@admin.register(NotificationLog)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'channel', 'status', 'created_at')
    list_filter = ('status', 'channel')
    search_fields = ('event__title', 'user__username')