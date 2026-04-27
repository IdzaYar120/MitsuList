import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            self.room_group_name = f'user_{self.user.id}_notifications'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event.get('title', 'Notification'),
            'message': event.get('message', ''),
            'link': event.get('link', ''),
        }))

class PartyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'party_{self.room_code}'
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')
        
        # Broadcast the action to everyone in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'party_action',
                'action': action,
                'data': text_data_json,
                'sender': self.user.username,
                'sender_id': self.user.id
            }
        )

    async def party_action(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'data': event['data'],
            'sender': event['sender'],
            'sender_id': event['sender_id']
        }))
