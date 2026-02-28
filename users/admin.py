from django.contrib import admin
from .models import Profile, SavedSearch, UserAnimeEntry, Follow

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme_preference', 'gender')
    search_fields = ('user__username',)
    list_filter = ('theme_preference', 'gender')

@admin.register(UserAnimeEntry)
class UserAnimeEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'score', 'updated_at')
    list_filter = ('status', 'score')
    search_fields = ('user__username', 'title')

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    search_fields = ('user__username', 'name')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following', 'created_at')
    search_fields = ('user__username', 'following__username')
