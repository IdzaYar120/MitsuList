from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Follow
from app.models import ReviewComment, Notification


@receiver(post_save, sender=Follow)
def notify_new_follower(sender, instance, created, **kwargs):
    """
    When a Follow is created, notify the target user.
    Moved here from users/views.py to keep views thin and logic centralised.
    """
    if created and instance.user != instance.following:
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.user,
            notification_type='new_follower',
            message=f"{instance.user.username} started following you",
            link=f"/profile/{instance.user.username}/",
        )


@receiver(post_save, sender=ReviewComment)
def notify_review_comment(sender, instance, created, **kwargs):
    """
    When a ReviewComment is created, notify the review author.
    Moved here from users/views.py.
    """
    if created and instance.user != instance.review.user:
        Notification.objects.create(
            recipient=instance.review.user,
            sender=instance.user,
            notification_type='review_comment',
            message=f"{instance.user.username} commented on your review",
            link=f"/anime/{instance.review.anime_id}/reviews/",
        )
