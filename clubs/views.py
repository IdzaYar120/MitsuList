from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Club, ClubRecommendation
from app.services import fetch_jikan_data

def club_list(request):
    clubs = Club.objects.select_related('owner', 'owner__profile').prefetch_related('members').order_by('-created_at')
    return render(request, 'clubs/club_list.html', {'clubs': clubs})

@login_required
def create_club(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        cover_image = request.FILES.get('cover_image')
        
        if not name:
            messages.error(request, "Club name is required.")
        elif Club.objects.filter(name=name).exists():
            messages.error(request, "A club with this name already exists.")
        else:
            club = Club.objects.create(
                name=name,
                description=description,
                owner=request.user
            )
            if cover_image:
                club.cover_image = cover_image
                club.save()
            
            # The owner automatically joins
            club.members.add(request.user)
            messages.success(request, f"Club '{club.name}' created successfully!")
            return redirect('clubs:club_detail', pk=club.pk)

    return render(request, 'clubs/create_club.html')

def club_detail(request, pk):
    club = get_object_or_404(Club.objects.select_related('owner', 'owner__profile').prefetch_related('members', 'members__profile', 'messages', 'messages__sender', 'messages__sender__profile'), pk=pk)
    is_member = request.user.is_authenticated and request.user in club.members.all()
    
    recommendations = club.recommendations.all().select_related('suggester', 'suggester__profile')
    
    context = {
        'club': club,
        'is_member': is_member,
        'recommendations': recommendations,
    }
    return render(request, 'clubs/club_detail.html', context)

@login_required
def join_club(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.user not in club.members.all():
        club.members.add(request.user)
        messages.success(request, f"You joined {club.name}!")
    return redirect('clubs:club_detail', pk=pk)

@login_required
def leave_club(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.user in club.members.all():
        if request.user == club.owner:
            messages.error(request, "The owner cannot leave the club. Delete the club instead.")
        else:
            club.members.remove(request.user)
            messages.info(request, f"You left {club.name}.")
    return redirect('clubs:club_detail', pk=pk)

@login_required
def recommend_anime(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.user not in club.members.all():
        messages.error(request, "You must be a member to recommend anime.")
        return redirect('clubs:club_detail', pk=pk)

    if request.method == 'POST':
        anime_id = request.POST.get('anime_id')
        reason = request.POST.get('reason', '')
        
        if not anime_id:
            messages.error(request, "Please provide an Anime ID.")
            return redirect('clubs:club_detail', pk=pk)
            
        try:
            anime_id = int(anime_id)
        except ValueError:
            messages.error(request, "Invalid Anime ID.")
            return redirect('clubs:club_detail', pk=pk)

        if ClubRecommendation.objects.filter(club=club, suggester=request.user, anime_id=anime_id).exists():
            messages.error(request, "You have already recommended this anime to this club.")
            return redirect('clubs:club_detail', pk=pk)

        # We must fetch the title and image from Jikan to store locally
        url = f"https://api.jikan.moe/v4/anime/{anime_id}"
        # We need to run sync code here or use httpx directly. We will use requests for simplicity since views are sync.
        import requests
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json().get('data', {})
                title = data.get('title')
                image_url = data.get('images', {}).get('jpg', {}).get('image_url')
                
                ClubRecommendation.objects.create(
                    club=club,
                    suggester=request.user,
                    anime_id=anime_id,
                    anime_title=title,
                    anime_image_url=image_url,
                    reason=reason
                )
                messages.success(request, f"Recommended {title} to the club!")
            else:
                messages.error(request, "Could not find anime via Jikan API.")
        except Exception as e:
            messages.error(request, "Failed to connect to Jikan API.")

    return redirect('clubs:club_detail', pk=pk)
