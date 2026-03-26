import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mitsulist.settings')
django.setup()

from users.models import Badge

initial_badges = [
    # Anime Count Badges
    {'name': 'Newbie', 'description': 'Watched 10+ anime', 'icon': 'fa-seedling', 'color': '#2ecc71', 'category': 'anime_count', 'req': 10},
    {'name': 'Otaku', 'description': 'Watched 50+ anime', 'icon': 'fa-glasses', 'color': '#3498db', 'category': 'anime_count', 'req': 50},
    {'name': 'Veteran', 'description': 'Watched 100+ anime', 'icon': 'fa-crown', 'color': '#f1c40f', 'category': 'anime_count', 'req': 100},
    
    # Completed Count Badges
    {'name': 'Completionist', 'description': 'Completed 50+ anime', 'icon': 'fa-check-double', 'color': '#9b59b6', 'category': 'completed_count', 'req': 50},
    {'name': 'Master', 'description': 'Completed 200+ anime', 'icon': 'fa-medal', 'color': '#e74c3c', 'category': 'completed_count', 'req': 200},
    
    # Review Count Badges
    {'name': 'Critic', 'description': 'Wrote 5 reviews', 'icon': 'fa-pen-nib', 'color': '#e67e22', 'category': 'review_count', 'req': 5},
    {'name': 'Top Reviewer', 'description': 'Wrote 20 reviews', 'icon': 'fa-star', 'color': '#f39c12', 'category': 'review_count', 'req': 20},
]

for b in initial_badges:
    Badge.objects.update_or_create(
        name=b['name'],
        defaults={
            'description': b['description'],
            'icon': b['icon'],
            'color': b['color'],
            'category': b['category'],
            'requirement_value': b['req']
        }
    )

print("Successfully populated default badges.")
