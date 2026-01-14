import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, Message, RoomParticipant

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        user = self.scope['user']
        if user.is_authenticated:
            # Check if user can access the room
            can_access = await self.check_room_access(user, self.room_id)
            if can_access:
                await self.accept()
                await self.send_user_list()
                await self.notify_user_joined(user)
            else:
                await self.close(code=4001)
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        user = self.scope['user']
        if user.is_authenticated:
            await self.notify_user_left(user)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        user = self.scope['user']
        
        if message_type == 'chat_message':
            message = data.get('message', '').strip()
            if message and user.is_authenticated:
                # Save message to database
                saved_message = await self.save_message(user, self.room_id, message)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': saved_message.id,
                        'sender_id': user.id,
                        'sender_username': user.username,
                        'message': message,
                        'timestamp': saved_message.timestamp.isoformat(),
                    }
                )
        
        elif message_type == 'typing':
            if user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': user.id,
                        'username': user.username,
                        'is_typing': data.get('is_typing', False)
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'message': event['message'],
            'timestamp': event['timestamp'],
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    # Helper methods
    @database_sync_to_async
    def check_room_access(self, user, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id, is_active=True)
            return room.participants.filter(id=user.id).exists() or user.is_staff
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, room_id, content):
        room = ChatRoom.objects.get(id=room_id)
        message = Message.objects.create(
            room=room,
            sender=user,
            content=content
        )
        return message

    async def send_user_list(self):
        users = await self.get_online_users(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': users
        }))

    @database_sync_to_async
    def get_online_users(self, room_id):
        room = ChatRoom.objects.get(id=room_id)
        participants = room.participants.all()
        return [{'id': p.id, 'username': p.username} for p in participants]

    async def notify_user_joined(self, user):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': user.id,
                'username': user.username
            }
        )

    async def notify_user_left(self, user):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': user.id,
                'username': user.username
            }
        )