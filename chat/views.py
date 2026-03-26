from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatThread, ChatMessage
from django.contrib.auth.models import User
from django.db.models import Q

@login_required
def inbox(request):
    """List all conversations for the current user."""
    threads = ChatThread.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).order_by('-updated_at')
    
    context = {
        'threads': threads
    }
    return render(request, 'chat/inbox.html', context)

@login_required
def room(request, thread_id):
    """View a specific chat conversation."""
    thread = get_object_or_404(ChatThread, id=thread_id)
    
    # Ensure current user is part of the thread
    if request.user != thread.user1 and request.user != thread.user2:
        return redirect('chat:inbox')
        
    messages = thread.messages.all()
    
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
