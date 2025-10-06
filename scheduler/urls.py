from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import EventViewSet, ReminderViewSet, NotificationLogViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename= 'event')
router.register(r'reminders', ReminderViewSet, basename= 'reminder')
router.register(r'notifications', NotificationLogViewSet, basename= 'notification')

urlpatterns = [
    path("", include(router.urls)),
]
