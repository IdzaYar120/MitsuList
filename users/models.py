from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorites = models.JSONField(default=list, blank=True)
    
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
        # Check if this is an existing instance to determine if image changed
        process_image = False
        if self.pk:
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.image != self.image:
                    process_image = True
            except Profile.DoesNotExist:
                process_image = True # Should be created
        else:
            process_image = True # New instance

        super().save(*args, **kwargs)
        
        if process_image and self.image:
            # Resize image if too large
            try:
                from PIL import Image
                img = Image.open(self.image.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except FileNotFoundError:
                pass  # Image file doesn't exist yet (e.g., during initial migration)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not resize profile image: {e}")

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
    anime_id = models.IntegerField(help_text="MAL Anime ID")
    title = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan_to_watch')
    score = models.IntegerField(default=0, help_text="User score 1-10")
    episodes_watched = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'anime_id')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.status})"

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
