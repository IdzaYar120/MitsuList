from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/save-search/', views.save_search, name='save-search'),
    path('api/saved-searches/', views.list_saved_searches, name='saved-searches'),
    path('api/anime/update/', views.update_anime_status, name='update_anime_status'),
    path('api/anime/status/<int:anime_id>/', views.get_user_anime_status, name='get_user_anime_status'),
    path('profile/review/', views.create_review, name='create_review'),
]
