import httpx
import asyncio
from django.core.cache import cache
import time
import logging

logger = logging.getLogger(__name__)

# Global semaphore to limit concurrent requests to Jikan API
# Jikan allows ~3 requests/second, so we allow 3 concurrent with small delays
jikan_semaphore = asyncio.Semaphore(3)
last_request_time = 0

async def fetch_jikan_data(cache_key, url, timeout=3600, retries=2):
    """
    Asynchronously fetch data from Jikan API with caching, throttling, and retry logic.
    Default timeout increased to 1 hour to reduce API hits.
    """
    global last_request_time
    
    # Check cache first
    data = cache.get(cache_key)
    if data:
        return data

    async with jikan_semaphore:
        # Small delay to spread requests (0.35s between each)
        current_time = time.time()
        time_since_last = current_time - last_request_time
        if time_since_last < 0.35:
            await asyncio.sleep(0.35 - time_since_last)
        
        async with httpx.AsyncClient() as client:
            for attempt in range(retries + 1):
                try:
                    last_request_time = time.time()
                    response = await client.get(url, timeout=15.0)
                    
                    if response.status_code == 200:
                        data = response.json()
                        cache.set(cache_key, data, timeout)
                        return data
                    
                    elif response.status_code == 429:
                        # Exponential backoff
                        wait_time = 2 ** (attempt + 1)
                        logger.warning(f"Rate limited on {url}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    elif 500 <= response.status_code < 600:
                         logger.warning(f"Server error {response.status_code} for {url}. Retrying...")
                         await asyncio.sleep(1)
                         continue
    
                    else:
                        logger.error(f"Error {response.status_code} for {url}")
                        break
                
                except httpx.RequestError as exc:
                    logger.error(f"Connection error: {exc}")
                    break
    
    return {'data': []}

async def fetch_anime_recommendations(cache_key, anime_id, timeout=86400):
    """
    Fetch recommendations for a specific anime.
    URl: https://api.jikan.moe/v4/anime/{id}/recommendations
    """
    url = f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations"
    return await fetch_jikan_data(cache_key, url, timeout)

def get_activity_feed(user):
    """
    Fetch activity feed for a user (actions of people they follow).
    """
    from users.models import UserAnimeEntry
    
    # Get users we follow
    # This triggers a DB call, so this function should be run in a thread/sync_to_async
    following_ids = user.following.values_list('following_id', flat=True)
    
    # Get entries from these users, ordered by update time
    return list(
        UserAnimeEntry.objects.filter(user_id__in=following_ids)
        .select_related('user', 'user__profile')
        .order_by('-updated_at')[:12]
    )
