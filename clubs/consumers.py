import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Club, ClubMessage
from django.contrib.auth.models import User

class ClubChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.club_id = self.scope['url_route']['kwargs']['club_id']
        self.room_group_name = f'club_chat_{self.club_id}'

        # Check if user is authenticated
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify the user is a member of the club
        is_member = await self.is_club_member(self.club_id, self.user)
        if not is_member:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json.get('message', '').strip()
        
        if not message_text:
            return

        # Save message to database
        saved_msg = await self.save_message(self.club_id, self.user, message_text)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender': self.user.username,
                'timestamp': saved_msg.timestamp.strftime('%H:%M'),
                'sender_id': self.user.id,
                'avatar_url': await self.get_user_avatar(self.user),
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']
        sender_id = event['sender_id']
        avatar_url = event['avatar_url']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp,
            'sender_id': sender_id,
            'avatar_url': avatar_url,
        }))

    @database_sync_to_async
    def is_club_member(self, club_id, user):
        try:
            club = Club.objects.get(id=club_id)
            return user in club.members.all()
        except Club.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, club_id, sender, text):
        club = Club.objects.get(id=club_id)
        msg = ClubMessage.objects.create(club=club, sender=sender, text=text)
        return msg

    @database_sync_to_async
    def get_user_avatar(self, user):
        try:
            return user.profile.avatar_url
        except Exception:
            return '/media/default.jpg'
