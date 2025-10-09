from django.urls import path
from .web_views import (
    event_list_view,
    event_create_view,
    event_detail_view,
)

app_name = "scheduler_web"

urlpatterns = [
    path("events/", event_list_view, name="events"),
    path("events/create/", event_create_view, name="event-create"),
    path("events/<int:pk>/", event_detail_view, name="event-detail"),
]
