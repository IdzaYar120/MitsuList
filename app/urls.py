from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("anime/<int:anime_id>/", views.anime_detail, name="anime-view"),
    path("api/search/", views.api_proxy_search, name="api-proxy"), # Changed to use query params
    path("api/genres/", views.get_genres, name="api-genres"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("feed/", views.activity_feed_view, name="activity-feed"),
    path("feed/global/", views.global_feed_view, name="global-feed"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("api/notifications/unread/", views.check_unread_notifications, name="api-notifications-unread"),
    path("discover/", views.discovery_view, name="discover"),
]