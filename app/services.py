import httpx
import asyncio
from django.core.cache import cache
import time
import logging

logger = logging.getLogger(__name__)

# Global semaphore storage to handle multiple event loops (Django/asgiref quirk)
_semaphores = {}

def get_jikan_semaphore():
    """Get or create a semaphore for the current event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.Semaphore(3) # Fallback if no loop (shouldn't happen in async view)
        
    if loop not in _semaphores:
        _semaphores[loop] = asyncio.Semaphore(3)
    return _semaphores[loop]

last_request_time = 0

# Jikan API Endpoints
JIKAN_API_ENDPOINTS = {
    'airing_now': 'https://api.jikan.moe/v4/seasons/now?limit=24',
    'top_anime': 'https://api.jikan.moe/v4/top/anime?limit=24',
    'popular_anime': 'https://api.jikan.moe/v4/top/anime?filter=bypopularity&limit=24',
    'anime_movie': 'https://api.jikan.moe/v4/top/anime?type=movie&limit=24',
    'anime_base': 'https://api.jikan.moe/v4/anime',
    'genres': 'https://api.jikan.moe/v4/genres/anime',
    'schedules': 'https://api.jikan.moe/v4/schedules',
}

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

    async with get_jikan_semaphore():
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
    URl: {JIKAN_API_ENDPOINTS['anime_base']}/{id}/recommendations
    """
    url = f"{JIKAN_API_ENDPOINTS['anime_base']}/{anime_id}/recommendations"
    return await fetch_jikan_data(cache_key, url, timeout)

async def get_daily_schedule(day):
    """
    Get schedule for a specific day with DB caching.
    """
    from .models import AnimeSchedule
    from asgiref.sync import sync_to_async
    from django.utils import timezone
    import datetime

    # 1. Try to get from DB
    get_schedule = sync_to_async(lambda: AnimeSchedule.objects.filter(day=day).first())
    schedule = await get_schedule()
    
    # Check if exists and fresh (< 24 hours)
    if schedule and (timezone.now() - schedule.updated_at) < datetime.timedelta(hours=24):
        return {'data': schedule.data}

    # 2. Fetch from API if missing or stale
    # We use a short cache key just for request stability (deduplication)
    url = f"{JIKAN_API_ENDPOINTS['schedules']}?filter={day}"
    data = await fetch_jikan_data(f"temp_schedule_{day}", url, timeout=60)
    
    anime_list = data.get('data', [])
    if anime_list:
        # Save to DB
        save_schedule = sync_to_async(lambda: AnimeSchedule.objects.update_or_create(
            day=day,
            defaults={'data': anime_list}
        ))
        await save_schedule()
        
    return data

async def fetch_schedule_data(cache_key='anime_schedule', timeout=86400):
   # Kept for backward compatibility if needed, but we should use get_daily_schedule
   return await get_daily_schedule('monday') # Placeholder

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
