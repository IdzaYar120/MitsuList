from django.shortcuts import render
import requests
from datetime import datetime
import math
import time
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit

from .models import News

def get_jikan_data(cache_key, url, timeout=300):
    """Helper to fetch data from Jikan with caching and throttling."""
    data = cache.get(cache_key)
    if data:
        return data

    # Safe throttling for Jikan (approx 3 requests/sec)
    time.sleep(0.35)
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cache.set(cache_key, data, timeout)
            return data
        elif response.status_code == 429:
            print(f"Rate limited on {url}")
        else:
            print(f"Error {response.status_code} for {url}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
    
    return {'data': []}

@ratelimit(key='ip', rate='20/m', method='GET', block=True)
def index(request):
    # Fetch News (Database)
    news_items = News.objects.all().order_by('-created_at')

    # Fetch API Data using helper
    airing_now_data = get_jikan_data('airing_now', 'https://api.jikan.moe/v4/seasons/now?limit=24')
    top_anime_data = get_jikan_data('top_anime', 'https://api.jikan.moe/v4/top/anime?limit=24')
    popular_anime_data = get_jikan_data('popular_anime', 'https://api.jikan.moe/v4/top/anime?filter=bypopularity&limit=24')
    anime_movie = get_jikan_data('anime_movie', 'https://api.jikan.moe/v4/top/anime?type=movie&limit=24')
        
    context = {
        'news_items': news_items,
        'airing_now_data': airing_now_data,
        'top_anime_data': top_anime_data,
        'popular_anime_data': popular_anime_data,
        'anime_movie': anime_movie
    }
    return render(request, 'index.html', context)

@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def index_two(request, anime_id):
    # Caching details too (10 minutes)
    cache_key = f'anime_detail_{anime_id}'
    raw_data = get_jikan_data(cache_key, f'https://api.jikan.moe/v4/anime/{anime_id}/full', timeout=600)
    
    anime_data = raw_data.get('data')
    if not anime_data or not isinstance(anime_data, dict):
        # If detail fetch fails or returns unexpected data, we can't render correctly
        return render(request, '404.html', status=404)

    # Data extraction with safe defaults
    media_type = anime_data.get('type', "N/A")
    episodes = anime_data.get('episodes', "N/A")
    status = anime_data.get('status', "N/A")
    source = anime_data.get('source', "N/A")
    rating = anime_data.get('rating', "N/A")
    episode_duration = anime_data.get('duration', "N/A")
    
    try:
        year = anime_data.get('year')
        season_name = anime_data.get('season', '')
        season = f"{season_name} {year}".strip().title() if (year or season_name) else "N/A"
    except:
        season = "N/A"
    
    relations = anime_data.get('relations', [])
    
    context = {
        'anime_data': anime_data,
        'relation_length': len(relations),
        'media_type': media_type,
        'episode_duration': episode_duration,
        'episodes': episodes,
        'status': status,
        'source': source,
        'season': season,
        'rating': rating,
    }
    return render(request, 'anime-view.html', context)

@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def index_three(request, search_query):
    from django.http import JsonResponse
    # Direct search proxy (could also be cached briefly)
    cache_key = f'search_{search_query.lower()}'
    data = get_jikan_data(cache_key, f'https://api.jikan.moe/v4/anime?q={search_query}&limit=10', timeout=60)
    return JsonResponse(data)

        
    