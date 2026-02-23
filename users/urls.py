from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/review/', views.create_review, name='create_review'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/save-search/', views.save_search, name='save-search'),
    path('api/saved-searches/', views.list_saved_searches, name='saved-searches'),
    path('api/update-status/', views.update_anime_status, name='update-status'),
    path('import/', views.import_list, name='import_list'),
    path('api/anime/status/<int:anime_id>/', views.get_user_anime_status, name='get_user_anime_status'),
    path('profile/review/', views.create_review, name='create_review'),
    
    # Review System
    path('anime/<int:anime_id>/reviews/', views.anime_reviews_list, name='anime_reviews_list'),
    path('reviews/<int:review_id>/like/', views.toggle_review_like, name='toggle_review_like'),
    path('reviews/<int:review_id>/comment/', views.add_review_comment, name='add_review_comment'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('reviews/comment/<int:comment_id>/delete/', views.delete_review_comment, name='delete_review_comment'),
    
    # Discord Integration
    path('discord/login/', views.discord_login, name='discord_login'),
    path('discord/callback/', views.discord_callback, name='discord_callback'),
    path('discord/disconnect/', views.discord_disconnect, name='discord_disconnect'),
    path('api/discord/presence/<str:discord_id>/', views.discord_presence_api, name='discord_presence_api'),
]

