from datetime import datetime, time
from django.conf import settings
from django.utils import timezone
import django_filters
from .models import Event

class EventFilter(django_filters.FilterSet):
    start_after = django_filters.IsoDateTimeFilter(field_name='start', lookup_expr='gte')
    end_before = django_filters.IsoDateTimeFilter(field_name='end', lookup_expr='lte')
    date = django_filters.DateFilter(method='filter_by_date')

    class Meta:
        model = Event
        fields = ['start_after', 'end_before', 'date', 'is_all_day']

    def filter_by_date(self, queryset, name, value):
        # Retorna eventos que tocam o dia 'value'
        if settings.USE_TZ:
            tz = timezone.get_current_timezone()
            start_day = timezone.make_aware(datetime.combine(value, time.min), tz)
            end_day = timezone.make_aware(datetime.combine(value, time.max), tz)
        else:
            start_day = datetime.combine(value, time.min)
            end_day = datetime.combine(value, time.max)

        return queryset.filter(end__gte=start_day, start__lte=end_day)
