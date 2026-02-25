from django.shortcuts import render
import requests
import asyncio
from datetime import datetime
import math
import time
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .services import fetch_jikan_data, JIKAN_API_ENDPOINTS

from .models import News, Review, Activity
from users.models import UserAnimeEntry
from .forms import ReviewForm
import random
import datetime
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
        fetch_jikan_data('airing_now', JIKAN_API_ENDPOINTS['airing_now']),
        fetch_jikan_data('top_anime', JIKAN_API_ENDPOINTS['top_anime']),
        fetch_jikan_data('popular_anime', JIKAN_API_ENDPOINTS['popular_anime']),
        fetch_jikan_data('anime_movie', JIKAN_API_ENDPOINTS['anime_movie'])
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
            
        # Activity Feed (Social)
        from .services import get_activity_feed
        # Wrap sync DB call
        get_feed_async = sync_to_async(get_activity_feed)
        activity_feed = await get_feed_async(request.user)
    else:
        activity_feed = []
        
    context = {
        'news_items': news_items,
        'airing_now_data': airing_now_data,
        'top_anime_data': top_anime_data,
        'popular_anime_data': popular_anime_data,
        'anime_movie': anime_movie,
        'recommendations_data': recommendations_data,
        'source_anime_title': source_anime_title,
        'activity_feed': activity_feed,
    }
    return render(request, 'index.html', context)

async def anime_detail(request, anime_id):
    # Fix for SynchronousOnlyOperation in template
    request.user = await request.auser()
    cache_key = f'anime_detail_{anime_id}'
    raw_data = await fetch_jikan_data(cache_key, f"{JIKAN_API_ENDPOINTS['anime_base']}/{anime_id}/full", timeout=600)
    
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
    
    # Translation Logic for Detail View
    from .translation import translate_anime_data
    from asgiref.sync import sync_to_async
    
    # Wrap sync translation logic
    translate_data_async = sync_to_async(translate_anime_data)
    anime_data = await translate_data_async(anime_data, get_language())
    
    # Update local variables from translated data
    status = anime_data.get('status')
    media_type = anime_data.get('type')
    source = anime_data.get('source')

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

async def api_proxy_search(request):
    from django.http import JsonResponse
    
    # Extract optional filters from query parameters
    search_query = request.GET.get('q', '')
    genres = request.GET.get('genres')
    year = request.GET.get('year')
    anime_type = request.GET.get('type') # 'tv', 'movie', etc.
    
    if not search_query and not genres and not year and not anime_type:
        return JsonResponse({'data': []})

    # Build Jikan Search URL
    base_url = f"{JIKAN_API_ENDPOINTS['anime_base']}?q={search_query}&limit=20"
    
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
    data = await fetch_jikan_data(cache_key, JIKAN_API_ENDPOINTS['genres'], timeout=86400)
    return JsonResponse(data)

async def calendar_view(request):
    """
    Display anime release calendar.
    """
    # Fix for SynchronousOnlyOperation
    request.user = await request.auser()
    
    from .services import get_daily_schedule
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Fetch schedule for each day in parallel
    # Now using get_daily_schedule which handles DB caching
    tasks = [get_daily_schedule(day) for day in days]
    day_results = await asyncio.gather(*tasks)
    
    today = datetime.datetime.now().strftime('%A').lower()
    
    # Highlight User's Anime
    user_watching_ids = set()
    if request.user.is_authenticated:
        from asgiref.sync import sync_to_async
        get_ids = sync_to_async(lambda: list(
            UserAnimeEntry.objects.filter(
                user=request.user, 
                status='watching'
            ).values_list('anime_id', flat=True)
        ))
        user_watching_ids = set(await get_ids())

    calendar_data = [] # List of (day_name, anime_list) tuples
    for i, day in enumerate(days):
        anime_list = day_results[i].get('data', [])
        
        # Mark anime as 'following'
        for anime in anime_list:
             if anime.get('mal_id') in user_watching_ids:
                anime['is_following'] = True
                
        calendar_data.append((day, anime_list))
                
    context = {
        'calendar_data': calendar_data,
        'today': today
    }
    return render(request, 'calendar.html', context)

async def activity_feed_view(request):
    """Feed of people you follow."""
    request.user = await request.auser()
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')

    from asgiref.sync import sync_to_async
    from django.core.paginator import Paginator

    # Fetch users we follow
    # Note: user.following is related name from Follow model
    def get_following_ids():
        return list(request.user.following.values_list('following_id', flat=True))
    
    get_following = sync_to_async(get_following_ids)
    following_ids = await get_following()

    # Fetch activities
    from .models import Activity
    activities_qs = Activity.objects.filter(user_id__in=following_ids).select_related('user', 'user__profile')
    
    # Pagination
    def paginate(qs, page_num):
        paginator = Paginator(qs, 20)
        return paginator.get_page(page_num)

    get_page = sync_to_async(paginate)
    page_obj = await get_page(activities_qs, request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'feed_type': 'following'
    }
    return render(request, 'activity.html', context)

async def global_feed_view(request):
    """Feed of everyone."""
    request.user = await request.auser()
    from asgiref.sync import sync_to_async
    from django.core.paginator import Paginator

    from .models import Activity
    activities_qs = Activity.objects.all().select_related('user', 'user__profile')
    
    # Pagination
    def paginate(qs, page_num):
        paginator = Paginator(qs, 20)
        return paginator.get_page(page_num)

    get_page = sync_to_async(paginate)
    page_obj = await get_page(activities_qs, request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'feed_type': 'global'
    }
    return render(request, 'activity.html', context)

    return render(request, 'activity.html', context)

async def notifications_view(request):
    """View to list user notifications."""
    request.user = await request.auser()
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')

    from asgiref.sync import sync_to_async
    from .models import Notification

    # Fetch all notifications for the user
    get_notifications = sync_to_async(lambda: list(
        Notification.objects.filter(recipient=request.user).select_related('sender', 'sender__profile')
    ))
    notifications = await get_notifications()

    # Mark them all as read when viewed? Or let the user click them?
    # Usually, viewing the drop down might not mark them, but visiting the page does.
    # Let's mark all as read automatically to keep it simple.
    @sync_to_async
    def mark_all_read():
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    await mark_all_read()

    context = {
        'notifications': notifications
    }
    return render(request, 'notifications.html', context)

async def check_unread_notifications(request):
    """AJAX endpoint to check unread notification count."""
    request.user = await request.auser()
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'unread': 0})
        
    from asgiref.sync import sync_to_async
    from .models import Notification
    
    get_unread = sync_to_async(lambda: Notification.objects.filter(recipient=request.user, is_read=False).count())
    count = await get_unread()
    
    return JsonResponse({'unread': count})