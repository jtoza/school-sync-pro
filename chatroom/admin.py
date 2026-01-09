from django.contrib import admin
from .models import ChatRoom, Message, RoomParticipant

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'created_by', 'created_at', 'is_active')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('participants',)
    actions = ['activate_rooms', 'deactivate_rooms']
    
    def activate_rooms(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} rooms activated.")
    activate_rooms.short_description = "Activate selected rooms"
    
    def deactivate_rooms(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} rooms deactivated.")
    deactivate_rooms.short_description = "Deactivate selected rooms"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read', 'room')
    search_fields = ('content', 'sender__username')
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(RoomParticipant)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'joined_at', 'is_admin')
    list_filter = ('is_admin', 'joined_at')
    search_fields = ('user__username', 'room__name')