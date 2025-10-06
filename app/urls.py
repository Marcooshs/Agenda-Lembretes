from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token

def health(_):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", TemplateView.as_view(template_name= 'home.html'), name= 'home'),
    path('health/', health, name= 'health'),
    path('api/auth/token/', obtain_auth_token, name= 'api-token'),
    path('api/', include('scheduler.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
