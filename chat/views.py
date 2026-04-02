from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatThread, ChatMessage
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def inbox(request):
    """List all conversations for the current user."""
    threads = ChatThread.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user1__profile', 'user2', 'user2__profile').order_by('-updated_at')
    
    context = {
        'threads': threads
    }
    return render(request, 'chat/inbox.html', context)

@login_required
def room(request, thread_id):
    """View a specific chat conversation."""
    thread = get_object_or_404(ChatThread.objects.select_related('user1', 'user1__profile', 'user2', 'user2__profile'), id=thread_id)
    
    # Ensure current user is part of the thread
    if request.user != thread.user1 and request.user != thread.user2:
        return redirect('chat:inbox')
        
    messages = list(thread.messages.all().select_related('sender', 'sender__profile').order_by('-timestamp')[:50])
    messages.reverse()
    
    # Determine the other user
    other_user = thread.user2 if request.user == thread.user1 else thread.user1

    context = {
        'thread': thread,
        'messages': messages,
        'other_user': other_user,
    }
    return render(request, 'chat/room.html', context)

@login_required
def start_chat(request, username):
    """Shortcut view to start a chat with a specific user."""
    other_user = get_object_or_404(User, username=username)
    
    if request.user == other_user:
        return redirect('chat:inbox') # Cannot chat with yourself
        
    # Get or create thread
    thread = ChatThread.objects.filter(
        (Q(user1=request.user) & Q(user2=other_user)) |
        (Q(user1=other_user) & Q(user2=request.user))
    ).first()
    
    if not thread:
        thread = ChatThread.objects.create(user1=request.user, user2=other_user)
        
    return redirect('chat:room', thread_id=thread.id)

@login_required
def get_messages(request, thread_id):
    """API endpoint to get paginated chat history."""
    thread = get_object_or_404(ChatThread, id=thread_id)
    if request.user != thread.user1 and request.user != thread.user2:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    page_number = request.GET.get('page', 1)
    messages_query = thread.messages.all().select_related('sender', 'sender__profile').order_by('-timestamp')
    paginator = Paginator(messages_query, 50)
    
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        return JsonResponse({'messages': [], 'has_next': False})
        
    messages_data = []
    # Reverse to keep chronological order within the prepended chunk
    for msg in reversed(page_obj.object_list):
        # Escape text to prevent XSS is good, but template parsing handles it normally. Since JSON is used, we'll escape on frontend.
        messages_data.append({
            'text': msg.text,
            'timestamp': msg.timestamp.strftime("%H:%M"),
            'sender': msg.sender.username,
            'avatar_url': msg.sender.profile.avatar_url,
            'is_sent': msg.sender == request.user
        })
        
    return JsonResponse({
        'messages': messages_data,
        'has_next': page_obj.has_next()
    })
