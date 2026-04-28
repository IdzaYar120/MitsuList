from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorites = models.JSONField(default=list, blank=True)
    
    # RPG Gamification
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # New Fields
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(blank=True, max_length=500)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='N')
    birth_date = models.DateField(null=True, blank=True)

    # Theme & Customization
    THEME_CHOICES = [
        ('dark', 'Dark Mode'),
        ('light', 'Light Mode'),
    ]
    ACCENT_CHOICES = [
        ('#7b2ff7', 'Mitsu Purple'),
        ('#ff6b6b', 'Ruby Red'),
        ('#4ecdc4', 'Mint Green'),
        ('#feca57', 'Sunset Orange'),
        ('#54a0ff', 'Ocean Blue'),
        ('#ff9ff3', 'Sakura Pink'),
    ]
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark')
    accent_color = models.CharField(max_length=10, choices=ACCENT_CHOICES, default='#7b2ff7')

    # Discord Integration
    discord_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    discord_username = models.CharField(max_length=255, blank=True, null=True)
    discord_access_token = models.CharField(max_length=255, blank=True, null=True)
    discord_refresh_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            try:
                img = Image.open(self.image)
                # Check if it's already a WebP or default image to skip processing
                if img.format != 'WEBP' and not self.image.name.endswith('default.jpg'):
                    output = BytesIO()
                    # Convert RGBA/P to RGB to avoid errors when saving to WEBP
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(output, format='WEBP', quality=80)
                    output.seek(0)
                    
                    # Generate new filename
                    filename = os.path.splitext(os.path.basename(self.image.name))[0] + '.webp'
                    self.image.save(filename, ContentFile(output.read()), save=False)
            except Exception as e:
                print(f"Error compressing profile image: {e}")
                
        super().save(*args, **kwargs)
        
    @property
    def xp_progress(self):
        return (self.xp % 200) / 200 * 100
        
    @property
    def xp_to_next_level(self):
        return 200 - (self.xp % 200)

    @property
    def avatar_url(self):
        try:
            url = self.image.url if self.image else ""
        except ValueError:
            return ""

        if "res.cloudinary.com" in url:
            parts = url.split('/upload/')
            if len(parts) == 2:
                return f"{parts[0]}/upload/w_300,h_300,c_fill,q_auto,f_auto/{parts[1]}"
        return url

class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    params = models.JSONField() # Stores filters like {q: '...', genres: [1,2], year: 2024}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class UserAnimeEntry(models.Model):
    STATUS_CHOICES = [
        ('watching', 'Watching'),
        ('completed', 'Completed'),
        ('plan_to_watch', 'Plan to Watch'),
        ('dropped', 'Dropped'),
        ('on_hold', 'On Hold'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anime_entries')
    anime_id = models.IntegerField(help_text="MAL Anime ID", db_index=True)
    title = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan_to_watch', db_index=True)
    score = models.IntegerField(default=0, help_text="User score 1-10")
    episodes_watched = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'anime_id')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.get_status_display()})"


class Badge(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=50) # e.g. 'fa-seedling'
    color = models.CharField(max_length=20, default='#2ecc71')
    category = models.CharField(max_length=50) # 'anime_count', 'review_count', 'completed_count'
    requirement_value = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, related_name='earned_badges', on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Follow(models.Model):
    user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'following'], name='unique_following')
        ]

    def __str__(self):
        return f"{self.user.username} follows {self.following.username}"

class CustomList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_lists')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    entries = models.ManyToManyField('UserAnimeEntry', related_name='in_custom_lists', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"
