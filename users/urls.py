from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/save-search/', views.save_search, name='save-search'),
    path('api/saved-searches/', views.list_saved_searches, name='saved-searches'),
]
