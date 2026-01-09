from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import ChatRoom, Message, RoomParticipant
from django.contrib.auth import get_user_model
import json

User = get_user_model()

@login_required
def chat_home(request):
    user = request.user
    rooms = ChatRoom.objects.filter(is_active=True)
    
    # Filter based on user type
    if user.is_staff:
        # Staff can see all rooms
        available_rooms = rooms
        my_rooms = rooms.filter(participants=user)
    else:
        # Students can only see rooms they're in and general rooms
        available_rooms = rooms.filter(
            Q(participants=user) | Q(room_type='general')
        ).distinct()
        my_rooms = rooms.filter(participants=user)
    
    context = {
        'available_rooms': available_rooms,
        'my_rooms': my_rooms,
        'user': user,
    }
    return render(request, 'chatroom/chat_home.html', context)

@login_required
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        room_type = request.POST.get('room_type', 'general')
        
        if not name:
            messages.error(request, "Room name is required")
            return redirect('chatroom:chat_home')
        
        # Create room
        room = ChatRoom.objects.create(
            name=name,
            description=description,
            room_type=room_type,
            created_by=request.user
        )
        
        # Add creator as participant
        room.participants.add(request.user)
        
        messages.success(request, f"Chat room '{name}' created successfully!")
        return redirect('chatroom:chat_room', room_id=room.id)
    
    return redirect('chatroom:chat_home')

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    # Check access
    if not room.participants.filter(id=request.user.id).exists() and not request.user.is_staff:
        messages.error(request, "You don't have permission to access this chat room")
        return redirect('chatroom:chat_home')
    
    # Get recent messages
    messages_list = room.messages.all().order_by('-timestamp')[:100]
    messages_list = reversed(list(messages_list))  # Show oldest first
    
    # Get participants
    participants = room.participants.all()
    
    context = {
        'room': room,
        'messages': messages_list,
        'participants': participants,
        'user': request.user,
    }
    return render(request, 'chatroom/chat_room.html', context)

@login_required
@require_POST
def get_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check access
    if not room.participants.filter(id=request.user.id).exists() and not request.user.is_staff:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    last_message_id = request.POST.get('last_message_id', 0)
    
    try:
        last_message_id = int(last_message_id)
    except ValueError:
        last_message_id = 0
    
    # Get new messages
    new_messages = room.messages.filter(id__gt=last_message_id).order_by('timestamp')
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_own': msg.sender.id == request.user.id
        })
    
    return JsonResponse({'messages': messages_data})

@login_required
@require_POST
def add_user_to_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Only room creator or staff can add users
    if request.user != room.created_by and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    room.participants.add(user)
    
    return JsonResponse({'success': True, 'username': user.username})

@login_required
@require_POST
def remove_user_from_room(request, room_id, user_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Only room creator or staff can remove users
    if request.user != room.created_by and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    room.participants.remove(user)
    
    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Only room creator or staff can delete
    if request.user != room.created_by and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this room")
        return redirect('chatroom:chat_home')
    
    room.is_active = False
    room.save()
    
    messages.success(request, f"Chat room '{room.name}' has been deleted")
    return redirect('chatroom:chat_home')