from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("app.urls")),
    path('users/', include('users.urls')),
    path("anime/id=<int:anime_id>", include("app.urls")),
    path("api-proxy/<str:search_query>", include("app.urls"))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
