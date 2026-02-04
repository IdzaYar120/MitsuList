from django.shortcuts import render
import requests
from datetime import datetime
import math
import time
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .services import fetch_jikan_data

from .models import News

async def get_jikan_data(cache_key, url, timeout=300):
    """Bridge for internal calls to the new async service."""
    return await fetch_jikan_data(cache_key, url, timeout)

@ratelimit(key='ip', rate='20/m', method='GET', block=True)
async def index(request):
    # Fetch News (Database - synchronous for now, Django handles it)
    from asgiref.sync import sync_to_async
    news_items = await sync_to_async(list)(News.objects.all().order_by('-created_at'))

    # Fetch API Data using new async helper
    airing_now_data = await fetch_jikan_data('airing_now', 'https://api.jikan.moe/v4/seasons/now?limit=24')
    top_anime_data = await fetch_jikan_data('top_anime', 'https://api.jikan.moe/v4/top/anime?limit=24')
    popular_anime_data = await fetch_jikan_data('popular_anime', 'https://api.jikan.moe/v4/top/anime?filter=bypopularity&limit=24')
    anime_movie = await fetch_jikan_data('anime_movie', 'https://api.jikan.moe/v4/top/anime?type=movie&limit=24')
        
    context = {
        'news_items': news_items,
        'airing_now_data': airing_now_data,
        'top_anime_data': top_anime_data,
        'popular_anime_data': popular_anime_data,
        'anime_movie': anime_movie
    }
    return render(request, 'index.html', context)

@ratelimit(key='ip', rate='60/m', method='GET', block=True)
async def index_two(request, anime_id):
    cache_key = f'anime_detail_{anime_id}'
    raw_data = await fetch_jikan_data(cache_key, f'https://api.jikan.moe/v4/anime/{anime_id}/full', timeout=600)
    
    anime_data = raw_data.get('data')
    if not anime_data or not isinstance(anime_data, dict):
        return render(request, '404.html', status=404)

    # Data extraction
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
async def index_three(request):
    from django.http import JsonResponse
    
    # Extract optional filters from query parameters
    search_query = request.GET.get('q', '')
    genres = request.GET.get('genres')
    year = request.GET.get('year')
    anime_type = request.GET.get('type') # 'tv', 'movie', etc.
    
    if not search_query and not genres and not year and not anime_type:
        return JsonResponse({'data': []})

    # Build Jikan Search URL
    base_url = f'https://api.jikan.moe/v4/anime?q={search_query}&limit=20'
    
    if genres:
        base_url += f'&genres={genres}'
    if year:
        base_url += f'&start_date={year}-01-01'
    if anime_type:
        base_url += f'&type={anime_type}'
    
    cache_key = f'search_advanced_{search_query.lower()}_{genres}_{year}_{anime_type}'
    data = await fetch_jikan_data(cache_key, base_url, timeout=60)
    return JsonResponse(data)

async def get_genres(request):
    from django.http import JsonResponse
    cache_key = 'anime_genres_list'
    data = await fetch_jikan_data(cache_key, 'https://api.jikan.moe/v4/genres/anime', timeout=86400)
    return JsonResponse(data)

        
    