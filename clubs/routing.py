from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/clubs/(?P<club_id>\d+)/$', consumers.ClubChatConsumer.as_asgi()),
]
