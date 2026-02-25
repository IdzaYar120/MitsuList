from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Activity, Review, ReviewLike
from users.models import UserAnimeEntry

@receiver(post_save, sender=UserAnimeEntry)
def track_status_update(sender, instance, created, **kwargs):
    # For status updates, we track both creation and changes
    # But only if it's not 'plan_to_watch' initially maybe? 
    # Actually, let's track everything for now.
    Activity.objects.create(
        user=instance.user,
        activity_type='status_update',
        anime_id=instance.anime_id,
        anime_title=instance.title,
        related_id=instance.id
    )

@receiver(post_save, sender=Review)
def track_new_review(sender, instance, created, **kwargs):
    if created:
        # Try to get anime title from UserAnimeEntry if possible
        anime_title = "Unknown Anime"
        entry = UserAnimeEntry.objects.filter(user=instance.user, anime_id=instance.anime_id).first()
        if entry:
            anime_title = entry.title
            
        Activity.objects.create(
            user=instance.user,
            activity_type='new_review',
            anime_id=instance.anime_id,
            anime_title=anime_title,
            related_id=instance.id
        )

@receiver(post_save, sender=ReviewLike)
def track_review_like(sender, instance, created, **kwargs):
    if created:
        Activity.objects.create(
            user=instance.user,
            activity_type='review_like',
            anime_id=instance.review.anime_id,
            # We need title here too.
            # Usually better to have anime title in Review model too, 
            # but let's fetch it for now.
            anime_title=f"Review by {instance.review.user.username}",
            related_id=instance.review.id
        )

        # Create a notification for the review owner (if it's not their own like)
        if instance.user != instance.review.user:
            from .models import Notification
            Notification.objects.create(
                recipient=instance.review.user,
                sender=instance.user,
                notification_type='review_like',
                message=f"{instance.user.username} liked your review.",
                link=f"/anime/{instance.review.anime_id}/reviews/"
            )
