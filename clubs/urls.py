from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.club_list, name='club_list'),
    path('create/', views.create_club, name='create_club'),
    path('<int:pk>/', views.club_detail, name='club_detail'),
    path('<int:pk>/join/', views.join_club, name='join_club'),
    path('<int:pk>/leave/', views.leave_club, name='leave_club'),
    path('<int:pk>/recommend/', views.recommend_anime, name='recommend_anime'),
]
