from django.contrib import admin
from .models import News, Review, ReviewLike, ReviewComment, TranslationCache, AnimeSchedule, Activity, Notification

# Customize the global admin title/header
admin.site.site_header = "MitsuList Administration"
admin.site.site_title = "MitsuList Admin Portal"
admin.site.index_title = "Welcome to MitsuList Management"

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'anime_id', 'created_at', 'updated_at')
    search_fields = ('user__username', 'content')
    list_filter = ('created_at',)

@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'created_at')
    search_fields = ('user__username',)

@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'created_at')
    search_fields = ('user__username', 'content')
    
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'anime_title', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'anime_title')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'message')

@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    list_display = ('source_text_hash', 'source_lang', 'target_lang', 'created_at')
    list_filter = ('target_lang', 'source_lang')

@admin.register(AnimeSchedule)
class AnimeScheduleAdmin(admin.ModelAdmin):
    list_display = ('day', 'updated_at')
    search_fields = ('day',)
