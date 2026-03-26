import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatThread, ChatMessage
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'

        # Check if user is authenticated
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify the user is part of the thread
        is_participant = await self.is_thread_participant(self.thread_id, self.user)
        if not is_participant:
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
        saved_msg = await self.save_message(self.thread_id, self.user, message_text)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender': self.user.username,
                'timestamp': saved_msg.timestamp.strftime('%H:%M'),
                'sender_id': self.user.id,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']
        sender_id = event['sender_id']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp,
            'sender_id': sender_id,
        }))

    @database_sync_to_async
    def is_thread_participant(self, thread_id, user):
        try:
            thread = ChatThread.objects.get(id=thread_id)
            return user == thread.user1 or user == thread.user2
        except ChatThread.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, thread_id, sender, text):
        thread = ChatThread.objects.get(id=thread_id)
        msg = ChatMessage.objects.create(thread=thread, sender=sender, text=text)
        # Update thread's updated_at timestamp implicitly via save
        thread.save() 
        return msg
