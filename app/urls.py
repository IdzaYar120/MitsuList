from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("anime/id=<int:anime_id>", views.index_two, name="anime-view"),
    path("api-proxy/", views.index_three, name="api-proxy"), # Changed to use query params
    path("api/genres/", views.get_genres, name="api-genres"),
]