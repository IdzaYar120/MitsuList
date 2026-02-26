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


async def get_smart_recommendations(user, limit=20):
    """
    Analyzes user's completed/watching animes and aggregates recommendations
    from Jikan API to provide personalized suggestions.
    """
    from users.models import UserAnimeEntry
    from asgiref.sync import sync_to_async
    from collections import defaultdict

    # 1. Fetch user's anime list
    @sync_to_async
    def get_user_anime():
        return list(UserAnimeEntry.objects.filter(user=user).values('anime_id', 'title', 'score', 'status'))
    
    user_anime_list = await get_user_anime()
    
    # Fast exit if list is empty
    if not user_anime_list:
        # Fallback: Just return popular anime
        return await fetch_jikan_data('popular_anime_fallback', JIKAN_API_ENDPOINTS['popular_anime']), []

    # Map of all IDs the user already has, so we don't recommend them
    user_anime_ids = {entry['anime_id'] for entry in user_anime_list}

    # Pick top N seed anime to base recommendations on.
    # We prefer highly scored or recently completed animes.
    sorted_seeds = sorted(
        [a for a in user_anime_list if a['status'] in ('completed', 'watching') and a['score'] is not None],
        key=lambda x: x['score'],
        reverse=True
    )
    
    # If no scored anime, just take any completed/watching
    if not sorted_seeds:
         sorted_seeds = [a for a in user_anime_list if a['status'] in ('completed', 'watching')]
         
    # Take top 5 seeds to avoid too many API calls
    seed_animes = sorted_seeds[:5]
    
    if not seed_animes:
        return await fetch_jikan_data('top_anime_fallback', JIKAN_API_ENDPOINTS['top_anime']), []

    # 2. Fetch recommendations for all seeds concurrently
    tasks = []
    for seed in seed_animes:
        cache_key = f"rec_{seed['anime_id']}"
        tasks.append(fetch_anime_recommendations(cache_key, seed['anime_id']))
        
    results = await asyncio.gather(*tasks)

    # 3. Aggregate results
    # We'll score recommendations by how many times they appear and from which seeds.
    rec_scores = defaultdict(lambda: {'score': 0, 'data': None, 'sources': []})
    
    for i, res in enumerate(results):
        seed_title = seed_animes[i]['title']
        recs = res.get('data', [])
        
        # Jikan sometimes returns hundreds, just take top 10 from each seed for aggregation
        for rec in recs[:15]:
            entry = rec.get('entry', {})
            rec_id = entry.get('mal_id')
            
            # Skip if user already watched it
            if not rec_id or rec_id in user_anime_ids:
                continue
                
            # Increase aggregation score (base + votes from Jikan)
            votes = rec.get('votes', 1)
            # Add some normalized weight
            weight = min(votes / 10.0, 5.0) + 1.0 
            
            rec_scores[rec_id]['score'] += weight
            rec_scores[rec_id]['data'] = entry
            
            # Track why it was recommended
            if seed_title not in rec_scores[rec_id]['sources']:
                rec_scores[rec_id]['sources'].append(seed_title)

    # 4. Sort aggregated results by score
    sorted_recs = sorted(rec_scores.values(), key=lambda x: x['score'], reverse=True)
    
    # Format the final list
    final_recommendations = []
    for item in sorted_recs[:limit]:
        # Build context string: "Because you liked X and Y"
        sources = item['sources']
        if len(sources) > 2:
            context = f"Because you liked {sources[0]}, {sources[1]}, and more"
        else:
            context = f"Because you liked {' and '.join(sources)}"
            
        final_recommendations.append({
            'anime': item['data'],
            'context': context
        })

    return None, final_recommendations

async def generate_wrapped_data(user, year):
    """
    Analyzes a user's anime list to generate 'Year in Review' statistics.
    Returns aggregated data like total episodes, average score, top animes, and a genre breakdown.
    """
    from users.models import UserAnimeEntry
    from asgiref.sync import sync_to_async
    import datetime
    from collections import Counter

    @sync_to_async
    def get_yearly_entries():
        # Get all entries updated in the specified year
        # We assume 'updated_at' roughly correlates with when they finished it or watched it
        return list(UserAnimeEntry.objects.filter(
            user=user,
            updated_at__year=year
        ).values('anime_id', 'title', 'score', 'episodes_watched', 'status', 'image_url'))

    entries = await get_yearly_entries()
    
    if not entries:
        return None  # No data for this year

    stats = {
        'total_completed': 0,
        'total_episodes': 0,
        'average_score': 0.0,
        'top_anime': [],
        'genres': [],
        'days_spent': 0.0
    }

    scored_entries_count = 0
    total_score = 0
    anime_ids_to_fetch_genres = []

    for entry in entries:
        stats['total_episodes'] += entry['episodes_watched']
        
        if entry['status'] == 'completed':
            stats['total_completed'] += 1
            
        if entry['score'] > 0:
            total_score += entry['score']
            scored_entries_count += 1
            
        # Collect IDs to fetch genres later
        anime_ids_to_fetch_genres.append(entry['anime_id'])

    # Calculate average score
    if scored_entries_count > 0:
        stats['average_score'] = round(total_score / scored_entries_count, 1)

    # Calculate approximate days spent (assuming 24 mins per episode)
    stats['days_spent'] = round((stats['total_episodes'] * 24.0) / (60.0 * 24.0), 1)

    # Find Top Anime (highest scored, then most episodes watched as tie-breaker)
    # We only want to highlight ones they actually scored highly
    top_candidates = sorted(
        [e for e in entries if e['score'] > 0], 
        key=lambda x: (x['score'], x['episodes_watched']), 
        reverse=True
    )
    
    # If no scored anime, just take the ones with most episodes watched
    if not top_candidates:
        top_candidates = sorted(
            entries, 
            key=lambda x: x['episodes_watched'], 
            reverse=True
        )

    stats['top_anime'] = top_candidates[:5] # Top 5

    # Fetch Genres concurrently for the top ~20 anime to build a genre profile
    genre_counter = Counter()
    
    # To keep API calls reasonable, we'll only fetch details for up to 20 anime
    # from their list to build the genre profile.
    sample_ids = anime_ids_to_fetch_genres[:20] 
    
    tasks = []
    for anime_id in sample_ids:
        # We use a long cache timeout (7 days) because anime genres rarely change
        cache_key = f"anime_details_{anime_id}"
        url = f"{JIKAN_API_ENDPOINTS['anime_base']}/{anime_id}"
        tasks.append(fetch_jikan_data(cache_key, url, timeout=604800))
        
    results = await asyncio.gather(*tasks)
    
    for res in results:
        data = res.get('data')
        if data and 'genres' in data:
            for g in data['genres']:
                genre_counter[g['name']] += 1
                
    # Top 3 genres
    stats['genres'] = [
        {'name': name, 'count': count} 
        for name, count in genre_counter.most_common(3)
    ]

    return stats
