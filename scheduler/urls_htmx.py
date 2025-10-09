from django.urls import path
from .web_views_htmx import (
    event_list,
    event_create,
    event_row,
    event_delete,
)

app_name = 'ui'

urlpatterns = [
    path('events/', event_list, name='events'),
    path('events/create/', event_create, name='event-create'),
    path('events/<int:pk>/row/', event_row, name='event-row'),
    path('events/<int:pk>/delete/', event_delete, name='event-delete'),
]
