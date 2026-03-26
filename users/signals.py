from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Follow, UserAnimeEntry, Badge, UserBadge
from app.models import ReviewComment, Notification, Review


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

@receiver(post_save, sender=UserAnimeEntry)
def check_anime_badges(sender, instance, created, **kwargs):
    """Evaluate and award badges based on Anime count."""
    user = instance.user
    total_entries = UserAnimeEntry.objects.filter(user=user).count()
    completed_entries = UserAnimeEntry.objects.filter(user=user, status='completed').count()
    
    # Check anime_count badges
    count_badges = Badge.objects.filter(category='anime_count', requirement_value__lte=total_entries)
    for badge in count_badges:
        user_badge, awarded = UserBadge.objects.get_or_create(user=user, badge=badge)
        if awarded:
            Notification.objects.create(
                recipient=user,
                sender=user,  # System message essentially
                notification_type='badge_earned',
                message=f"🏆 You earned a new badge: {badge.name}!",
                link=f"/users/profile/",
            )
            
    # Check completed_count badges
    completed_badges = Badge.objects.filter(category='completed_count', requirement_value__lte=completed_entries)
    for badge in completed_badges:
        user_badge, awarded = UserBadge.objects.get_or_create(user=user, badge=badge)
        if awarded:
            Notification.objects.create(
                recipient=user,
                sender=user,
                notification_type='badge_earned',
                message=f"🏆 You earned a new badge: {badge.name}!",
                link=f"/users/profile/",
            )

@receiver(post_save, sender=Review)
def check_review_badges(sender, instance, created, **kwargs):
    """Evaluate and award badges based on Review count."""
    user = instance.user
    total_reviews = Review.objects.filter(user=user).count()
    
    review_badges = Badge.objects.filter(category='review_count', requirement_value__lte=total_reviews)
    for badge in review_badges:
        user_badge, awarded = UserBadge.objects.get_or_create(user=user, badge=badge)
        if awarded:
            Notification.objects.create(
                recipient=user,
                sender=user,
                notification_type='badge_earned',
                message=f"🏆 You earned a new badge: {badge.name}!",
                link=f"/users/profile/",
            )
