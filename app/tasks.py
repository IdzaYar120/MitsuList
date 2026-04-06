import time
import requests
import logging
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from users.models import UserAnimeEntry

logger = logging.getLogger(__name__)

@shared_task
def import_mal_username_task(user_id, mal_username):
    """
    Background Celery worker to import MAL user list via Jikan API.
    Handles pagination sequentially.
    """
    # MAL API status mapping
    status_map = {
        1: 'watching',
        2: 'completed',
        3: 'on_hold',
        4: 'dropped',
        6: 'plan_to_watch'
    }

    try:
        user = User.objects.get(id=user_id)
        has_next_page = True
        page = 1
        count = 0
        
        while has_next_page:
            url = f"https://api.jikan.moe/v4/users/{mal_username}/animelist/all?page={page}"
            response = requests.get(url, timeout=15.0)
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get('data', [])
                
                for entry in entries:
                    anime = entry.get('anime', {})
                    mal_id = anime.get('mal_id')
                    title = anime.get('title')
                    images = anime.get('images', {}).get('jpg', {}).get('image_url', '')
                    
                    my_status = entry.get('watching_status', 6)
                    my_score = entry.get('score', 0)
                    my_episodes = entry.get('episodes_watched', 0)
                    
                    db_status = status_map.get(my_status, 'plan_to_watch')
                    
                    UserAnimeEntry.objects.update_or_create(
                        user=user,
                        anime_id=mal_id,
                        defaults={
                            'title': title,
                            'status': db_status,
                            'score': my_score,
                            'episodes_watched': my_episodes,
                            'image_url': images,
                            'updated_at': timezone.now()
                        }
                    )
                    count += 1
                
                pagination = data.get('pagination', {})
                has_next_page = pagination.get('has_next_page', False)
                page += 1
                
                # Sleep to respect Jikan's strict rate limits (3 req/sec)
                time.sleep(0.5)
                
            elif response.status_code == 429:
                logger.warning(f"Rate limited during MAL background import. Retrying...")
                time.sleep(2) # Backoff
            elif response.status_code == 404:
                logger.warning(f"MAL user {mal_username} not found via background import.")
                break
            else:
                logger.warning(f"Failed to fetch MAL list for {mal_username}. Status: {response.status_code}")
                break
                
        logger.info(f"Successfully imported {count} anime for user {user.username} from MAL username {mal_username}")
        
    except Exception as e:
        logger.error(f"Background MAL import error: {e}")
