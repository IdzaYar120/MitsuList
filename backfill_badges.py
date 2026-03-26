import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mitsulist.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import UserAnimeEntry, Badge, UserBadge
from app.models import Review

users = User.objects.all()
for user in users:
    # Anime badges
    total_entries = UserAnimeEntry.objects.filter(user=user).count()
    count_badges = Badge.objects.filter(category='anime_count', requirement_value__lte=total_entries)
    for badge in count_badges:
        UserBadge.objects.get_or_create(user=user, badge=badge)
        
    completed_entries = UserAnimeEntry.objects.filter(user=user, status='completed').count()
    completed_badges = Badge.objects.filter(category='completed_count', requirement_value__lte=completed_entries)
    for badge in completed_badges:
        UserBadge.objects.get_or_create(user=user, badge=badge)
        
    # Review badges
    total_reviews = Review.objects.filter(user=user).count()
    review_badges = Badge.objects.filter(category='review_count', requirement_value__lte=total_reviews)
    for badge in review_badges:
        UserBadge.objects.get_or_create(user=user, badge=badge)

print("Badges backfilled recursively for all historical user progress.")
