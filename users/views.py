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
    from django.core.paginator import Paginator
    
    anime_entries_list = UserAnimeEntry.objects.filter(user=request.user)
    paginator = Paginator(anime_entries_list, 24)  # 24 items per page
    
    page_number = request.GET.get('page')
    anime_entries = paginator.get_page(page_number)
    
    return render(request, 'users/profile.html', {'anime_entries': anime_entries})

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
