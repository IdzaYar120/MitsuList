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
    anime_id = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.anime_id}'


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
    
    def __str__(self):
        return f"{self.day} schedule"
