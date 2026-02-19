from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from .models import SavedSearch, UserAnimeEntry
from app.models import Review
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from app.forms import ReviewForm
from app.models import Review, ReviewLike, ReviewComment
from django.shortcuts import get_object_or_404
from django.db.models import Count, Exists, OuterRef
import datetime

@login_required
def save_search(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', 'Untitled Search')
            params = data.get('params', {})
            
            SavedSearch.objects.create(user=request.user, name=name, params=params)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@login_required
def list_saved_searches(request):
    searches = SavedSearch.objects.filter(user=request.user)
    data = [{'id': s.id, 'name': s.name, 'params': s.params, 'created_at': s.created_at} for s in searches]
    return JsonResponse({'data': data})

@login_required
def profile(request):
    return redirect('public_profile', username=request.user.username)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/edit_profile.html', context)

@login_required
def update_anime_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            anime_id = data.get('anime_id')
            status = data.get('status')
            score = data.get('score', 0)
            episodes_watched = data.get('episodes_watched', 0)
            title = data.get('title', 'Unknown Title')
            image_url = data.get('image_url', '')

            if not anime_id or not status:
                return JsonResponse({'status': 'error', 'message': 'Missing fields'}, status=400)

            entry, created = UserAnimeEntry.objects.update_or_create(
                user=request.user,
                anime_id=anime_id,
                defaults={
                    'status': status,
                    'score': score,
                    'episodes_watched': episodes_watched,
                    'title': title,
                    'image_url': image_url
                }
            )
            return JsonResponse({'status': 'success', 'entry_id': entry.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@login_required
def get_user_anime_status(request, anime_id):
    try:
        entry = UserAnimeEntry.objects.get(user=request.user, anime_id=anime_id)
        return JsonResponse({
            'found': True,
            'status': entry.status,
            'score': entry.score,
            'episodes_watched': entry.episodes_watched
        })
    except UserAnimeEntry.DoesNotExist:
        return JsonResponse({'found': False})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

@login_required
def create_review(request):
    # Get anime list for dropdown (only from user's list)
    user_anime_list = UserAnimeEntry.objects.filter(user=request.user).values('anime_id', 'title')
    
    if request.method == 'POST':
        anime_id = request.POST.get('anime_id')
        content = request.POST.get('content')
        
        if not anime_id or not content:
            messages.error(request, "Please select an anime and write a review.")
        else:
            # Verify anime is in user's list
            if not UserAnimeEntry.objects.filter(user=request.user, anime_id=anime_id).exists():
                messages.error(request, "You can only review anime from your list.")
            # Check for existing review
            elif Review.objects.filter(user=request.user, anime_id=anime_id).exists():
                messages.error(request, "You have already reviewed this anime.")
            else:
                Review.objects.create(
                    user=request.user,
                    anime_id=anime_id,
                    content=content
                )
                messages.success(request, "Review posted successfully!")
                return redirect('profile')

    return render(request, 'users/create_review.html', {'user_anime_list': user_anime_list})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("home")

@login_required
def follow_user(request, username):
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import User
    from .models import Follow
    
    target_user = get_object_or_404(User, username=username)
    
    if target_user != request.user:
        Follow.objects.get_or_create(user=request.user, following=target_user)
        # messages.success(request, f"You are now following {target_user.username}")
        
    return redirect('public_profile', username=username)

@login_required
def unfollow_user(request, username):
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import User
    from .models import Follow
    
    target_user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, following=target_user).delete()
    # messages.info(request, f"You have unfollowed {target_user.username}")
        
    return redirect('public_profile', username=username)

def public_profile(request, username):
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import User
    from .models import Follow
    from django.core.paginator import Paginator
    
    viewed_user = get_object_or_404(User, username=username)
    
    # Get anime list
    anime_entries_list = UserAnimeEntry.objects.filter(user=viewed_user)
    paginator = Paginator(anime_entries_list, 24)
    page_number = request.GET.get('page')
    anime_entries = paginator.get_page(page_number)
    
    # Follow stats
    followers_count = Follow.objects.filter(following=viewed_user).count()
    following_count = Follow.objects.filter(user=viewed_user).count()
    
    is_following = False
    is_following = False
    shared_anime = []
    
    # --- Statistics Calculation ---
    from django.db.models import Sum, Avg
    
    stats = {
        'total_entries': anime_entries_list.count(),
        'watching': anime_entries_list.filter(status='watching').count(),
        'completed': anime_entries_list.filter(status='completed').count(),
        'on_hold': anime_entries_list.filter(status='on_hold').count(),
        'dropped': anime_entries_list.filter(status='dropped').count(),
        'plan_to_watch': anime_entries_list.filter(status='plan_to_watch').count(),
        'total_episodes': anime_entries_list.aggregate(Sum('episodes_watched'))['episodes_watched__sum'] or 0,
        'mean_score': round(anime_entries_list.exclude(score=0).aggregate(Avg('score'))['score__avg'] or 0.0, 1),
    }
    
    # Calculate Days Watched (Approximation: 24 min per episode)
    minutes_watched = stats['total_episodes'] * 24
    stats['days_watched'] = round(minutes_watched / 60 / 24, 1)
    
    # --- Badges ---
    badges = []
    if stats['total_entries'] >= 10:
        badges.append({'name': 'Newbie', 'icon': 'fa-seedling', 'color': '#2ecc71', 'desc': 'Watched 10+ anime'})
    if stats['total_entries'] >= 50:
        badges.append({'name': 'Otaku', 'icon': 'fa-glasses', 'color': '#3498db', 'desc': 'Watched 50+ anime'})
    if stats['total_entries'] >= 100:
        badges.append({'name': 'Veteran', 'icon': 'fa-crown', 'color': '#f1c40f', 'desc': 'Watched 100+ anime'})
    if stats['completed'] >= 50:
        badges.append({'name': 'Completionist', 'icon': 'fa-check-double', 'color': '#9b59b6', 'desc': 'Completed 50+ anime'})
    
    if request.user.is_authenticated:
        if request.user != viewed_user:
            is_following = Follow.objects.filter(user=request.user, following=viewed_user).exists()
            
            # Shared Anime Logic
            viewed_user_anime_ids = UserAnimeEntry.objects.filter(user=viewed_user).values_list('anime_id', flat=True)
            shared_anime = UserAnimeEntry.objects.filter(
                user=request.user, 
                anime_id__in=viewed_user_anime_ids
            ).select_related('user')[:5] # Limit to 5 for preview
            
    # --- Activity History ---
    recent_updates = anime_entries_list.order_by('-updated_at')[:5]
    
    context = {
        'viewed_user': viewed_user,
        'anime_entries': anime_entries,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_own_profile': request.user == viewed_user,
        'shared_anime': shared_anime,
        'stats': stats,
        'badges': badges,
        'recent_updates': recent_updates,
    }
    return render(request, 'users/profile.html', context)
@login_required
def import_list(request):
    if request.method == 'POST':
        xml_file = request.FILES.get('xml_file')
        if not xml_file or not xml_file.name.endswith('.xml'):
            messages.error(request, 'Please upload a valid .xml file.')
            return redirect('import_list')
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # MAL Status to MitsuList Status Mapping
            status_map = {
                'Watching': 'watching',
                'Completed': 'completed',
                'On-Hold': 'on_hold',
                'Dropped': 'dropped',
                'Plan to Watch': 'plan_to_watch'
            }
            
            count = 0
            for anime in root.findall('anime'):
                mal_id = int(anime.find('series_animedb_id').text)
                title = anime.find('series_title').text
                my_status = anime.find('my_status').text
                my_score = int(anime.find('my_score').text)
                my_episodes = int(anime.find('my_watched_episodes').text)
                
                # Default status if unknown
                db_status = status_map.get(my_status, 'plan_to_watch')
                
                # Update or Create
                UserAnimeEntry.objects.update_or_create(
                    user=request.user,
                    anime_id=mal_id,
                    defaults={
                        'title': title, # We save title to avoid API lookups for simple lists
                        'status': db_status,
                        'score': my_score,
                        'episodes_watched': my_episodes,
                        'updated_at': datetime.datetime.now()
                    }
                )
                count += 1
                
            messages.success(request, f'Successfully imported {count} anime entries!')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Error parsing file: {e}')
            return redirect('import_list')
            
    return render(request, 'users/import.html')

def anime_reviews_list(request, anime_id):
    # Get anime details (simplified, no full API call needed if we just show reviews, 
    # but we need title. For now let's rely on what we have in DB or pass basic info)
    # Actually, we should probably fetch basic info or at least have a robust template.
    # For now, let's just fetch reviews.
    
    reviews = Review.objects.filter(anime_id=anime_id).select_related('user', 'user__profile').annotate(
        likes_count=Count('likes'),
        is_liked=Exists(ReviewLike.objects.filter(review=OuterRef('pk'), user=request.user)) if request.user.is_authenticated else Value(False)
    ).order_by('-created_at')
    
    # We might need anime title. Let's try to get it from one of the reviews or UserAnimeEntry
    anime_title = "Anime Reviews"
    if reviews.exists():
        # Try to find an entry for this anime to get title
        entry = UserAnimeEntry.objects.filter(anime_id=anime_id).first()
        if entry:
            anime_title = entry.title

    context = {
        'reviews': reviews,
        'anime_id': anime_id,
        'anime_title': anime_title
    }
    return render(request, 'users/anime_reviews.html', context)

@login_required
def toggle_review_like(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)
        like, created = ReviewLike.objects.get_or_create(user=request.user, review=review)
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
            
        return JsonResponse({'liked': liked, 'count': review.likes.count()})
    return JsonResponse({'status': 'invalid'}, status=400)

@login_required
def add_review_comment(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)
        content = request.POST.get('content')
        if content:
            ReviewComment.objects.create(user=request.user, review=review, content=content)
            messages.success(request, 'Comment added!')
        else:
            messages.error(request, 'Comment cannot be empty.')
            
    return redirect('anime_reviews_list', anime_id=review.anime_id)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user == review.user:
        anime_id = review.anime_id
        review.delete()
        messages.success(request, 'Review deleted.')
        return redirect('anime-view', anime_id=anime_id)
    else:
        messages.error(request, 'You cannot delete this review.')
        return redirect('anime-view', anime_id=review.anime_id)

@login_required
def delete_review_comment(request, comment_id):
    comment = get_object_or_404(ReviewComment, id=comment_id)
    if request.user == comment.user or request.user == comment.review.user:
        review_id = comment.review.id
        anime_id = comment.review.anime_id
        comment.delete()
        messages.success(request, 'Comment deleted.')
        return redirect('anime_reviews_list', anime_id=anime_id)
    return redirect('home')
