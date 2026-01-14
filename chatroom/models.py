from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('class', 'Class Room'),
        ('group', 'Study Group'),
        ('staff', 'Staff Room'),
        ('general', 'General Chat'),
        ('project', 'Project Group'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='general')
    participants = models.ManyToManyField(User, related_name='chatrooms')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chatrooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_create_room', 'Can create chat room'),
            ('can_delete_room', 'Can delete chat room'),
            ('can_manage_room', 'Can manage chat room'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class RoomParticipant(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='room_participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participating_rooms')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['room', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.room.name}"