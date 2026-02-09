from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("anime/<int:anime_id>/", views.anime_detail, name="anime-view"),
    path("api/search/", views.api_proxy_search, name="api-proxy"), # Changed to use query params
    path("api/genres/", views.get_genres, name="api-genres"),
]