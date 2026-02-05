from django.shortcuts import render
import requests
import asyncio
from datetime import datetime
import math
import time
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .services import fetch_jikan_data

from .models import News, Review
from users.models import UserAnimeEntry
from .forms import ReviewForm
import random
from django.utils.translation import get_language
from .translation import translate_text

async def get_jikan_data(cache_key, url, timeout=300):
    """Bridge for internal calls to the new async service."""
    return await fetch_jikan_data(cache_key, url, timeout)

async def index(request):
    # Fix for SynchronousOnlyOperation in template
    request.user = await request.auser()
    # Fetch News (Database - synchronous for now, Django handles it)
    from asgiref.sync import sync_to_async
    news_items = await sync_to_async(list)(News.objects.all().order_by('-created_at'))

    # Fetch API Data using new async helper
    airing_now_data, top_anime_data, popular_anime_data, anime_movie = await asyncio.gather(
        fetch_jikan_data('airing_now', 'https://api.jikan.moe/v4/seasons/now?limit=24'),
        fetch_jikan_data('top_anime', 'https://api.jikan.moe/v4/top/anime?limit=24'),
        fetch_jikan_data('popular_anime', 'https://api.jikan.moe/v4/top/anime?filter=bypopularity&limit=24'),
        fetch_jikan_data('anime_movie', 'https://api.jikan.moe/v4/top/anime?type=movie&limit=24')
    )

    # Title translation disabled - anime names should stay in original language
    # (Literal translation looks bad for proper nouns)
    # Translation is still available for status, synopsis, etc. on detail pages
    recommendations_data = None
    source_anime_title = None
    
    if request.user.is_authenticated:
        # Get user's completed or watching anime
        user_entries = await sync_to_async(list)(
            UserAnimeEntry.objects.filter(
                user=request.user, 
                status__in=['completed', 'watching']
            ).values('anime_id', 'title')
        )
        
        if user_entries:
            # Pick a random one for variety
            random_entry = random.choice(user_entries)
            source_id = random_entry['anime_id']
            source_anime_title = random_entry['title']
            
            # Fetch recommendations
            from .services import fetch_anime_recommendations
            rec_key = f'rec_{source_id}'
            recommendations_data = await fetch_anime_recommendations(rec_key, source_id)
        
    context = {
        'news_items': news_items,
        'airing_now_data': airing_now_data,
        'top_anime_data': top_anime_data,
        'popular_anime_data': popular_anime_data,
        'anime_movie': anime_movie,
        'recommendations_data': recommendations_data,
        'source_anime_title': source_anime_title,
    }
    return render(request, 'index.html', context)

async def index_two(request, anime_id):
    # Fix for SynchronousOnlyOperation in template
    request.user = await request.auser()
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
    
    # Translation Logic for Detail View - Uses database-backed cache
    # Note: Title is NOT translated (proper nouns shouldn't be translated literally)
    current_lang = get_language()
    if current_lang == 'uk':
        from asgiref.sync import sync_to_async
        translate_sync = sync_to_async(translate_text)
        
        # Translate synopsis and metadata (but NOT title)
        anime_data['synopsis'] = await translate_sync(anime_data.get('synopsis'), 'uk')
        anime_data['status'] = await translate_sync(anime_data.get('status'), 'uk')
        anime_data['type'] = await translate_sync(anime_data.get('type'), 'uk')
        anime_data['source'] = await translate_sync(anime_data.get('source'), 'uk')
        
        # Update local variables
        status = anime_data.get('status')
        media_type = anime_data.get('type')
        source = anime_data.get('source')
        
        # Translate Genres
        if 'genres' in anime_data:
            for genre in anime_data['genres']:
                genre['name'] = await translate_sync(genre.get('name'), 'uk')

    # Review Logic
    from asgiref.sync import sync_to_async
    
    get_reviews = sync_to_async(lambda: list(Review.objects.filter(anime_id=anime_id).order_by('-created_at').select_related('user')))
    reviews = await get_reviews()
    
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        # Check if user already reviewed
        get_existing_review = sync_to_async(lambda: Review.objects.filter(user=request.user, anime_id=anime_id).first())
        existing_review = await get_existing_review()
        
        if existing_review:
            user_review = existing_review

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
        'reviews': reviews,
        'review_form': review_form,
        'user_review': user_review,
    }
    return render(request, 'anime-view.html', context)

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

        
    