from django.db import models
from django.contrib.auth.models import User

class Club(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, max_length=1500)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_clubs')
    members = models.ManyToManyField(User, related_name='joined_clubs', blank=True)
    cover_image = models.ImageField(upload_to='club_covers/', default='default_club.jpg', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ClubMessage(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='club_messages')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.club.name}] {self.sender.username}: {self.text[:20]}"

class ClubRecommendation(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='recommendations')
    suggester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='club_recommendations')
    anime_id = models.IntegerField(db_index=True)
    anime_title = models.CharField(max_length=255)
    anime_image_url = models.URLField(max_length=500, blank=True, null=True)
    reason = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A user can suggest a specific anime to a specific club only once
        unique_together = ('club', 'suggester', 'anime_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.suggester.username} recommended {self.anime_title} to {self.club.name}"
