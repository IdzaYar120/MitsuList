from django.db import models

class News(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='news_images/')
    description = models.TextField(blank=True)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "News"

from django.contrib.auth.models import User

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anime_id = models.IntegerField(db_index=True)
    content = models.TextField()
    is_spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.anime_id}'

    @property
    def like_count(self):
        return self.likes.count()

class ReviewLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.username} likes review {self.review.id}"

class ReviewComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.user.username} on review {self.review.id}"


class TranslationCache(models.Model):
    """
    Persistent cache for translations.
    First translation is slow (calls Google), all subsequent are instant (from DB).
    """
    source_text_hash = models.CharField(max_length=32, db_index=True)  # MD5 hash
    source_lang = models.CharField(max_length=10, default='en')
    target_lang = models.CharField(max_length=10)
    translated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('source_text_hash', 'target_lang')
        indexes = [
            models.Index(fields=['source_text_hash', 'target_lang']),
        ]
    
    def __str__(self):
        return f'{self.source_text_hash[:8]}... -> {self.target_lang}'

class AnimeSchedule(models.Model):
    """
    Stores daily anime release schedules to reduce API usage.
    """
    day = models.CharField(max_length=20, unique=True, db_index=True) # monday, tuesday, etc.
    data = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)
    

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('status_update', 'Status Update'),
        ('new_review', 'New Review'),
        ('review_like', 'Review Like'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, db_index=True)
    anime_id = models.IntegerField(db_index=True)
    anime_title = models.CharField(max_length=255)
    related_id = models.IntegerField(null=True, blank=True) # ID of review/entry
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Activities"

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.anime_title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('review_like', 'Review Like'),
        ('review_comment', 'Review Comment'),
        ('new_follower', 'New Follower'),
        ('system', 'System Message'),
        ('badge_earned', 'Badge Earned'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    link = models.URLField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username} - {self.notification_type} - Read: {self.is_read}"

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.recipient.id}_notifications',
            {
                'type': 'send_notification',
                'title': instance.get_notification_type_display(),
                'message': instance.message,
                'link': instance.link or '',
            }
        )

class AnimeMetadata(models.Model):
    mal_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True)
    episodes = models.IntegerField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    media_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    studios = models.JSONField(default=list, blank=True)
    genres = models.JSONField(default=list, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mal_id} - {self.title}"
