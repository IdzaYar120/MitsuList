from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:thread_id>/', views.room, name='room'),
    path('start/<str:username>/', views.start_chat, name='start_chat'),
]
