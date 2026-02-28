from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("app.urls")),
    path('i18n/', include('django.conf.urls.i18n')),
    path('users/', include('users.urls')),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
