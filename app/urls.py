from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db import connection
from rest_framework.authtoken.views import obtain_auth_token


def health(_):
    return JsonResponse({
        'status': 'ok',
        'db': connection.vendor,
        'engine': connection.settings_dict['ENGINE'],
        'name': connection.settings_dict['NAME'],
    })


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home (template opcional)
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Health-check com info do DB
    path('health/', health, name='health'),

    # Auth por token (DRF)
    path('api/auth/token/', obtain_auth_token, name='api-token'),

    # API REST
    path('api/', include('scheduler.urls')),

    # UI Web (Bootstrap) - precisa do arquivo scheduler/urls_web.py
    path('web/', include(('scheduler.urls_web', 'scheduler_web'), namespace='scheduler_web')),

    # UI HTMX (leve e moderna) - precisa do arquivo scheduler/urls_web.py
    path('ui/', include(('scheduler.urls_htmx', 'ui'), namespace='ui')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
