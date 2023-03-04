import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

from .models import Message
from posts.models import Group


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.group_group_name = 'chat_%s' % self.group_name

        await self.channel_layer.group_add(
            self.group_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self):
        await self.channel_layer.group_discard(
            self.group_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        group = data['group']

        await self.save_message(username, group, message)

        await self.channel_layer.group_send(
            self.group_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'group': group,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        group = event['group']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'group': group,
        }))

    @sync_to_async
    def save_message(self, username, group, message):
        user = User.objects.get(username=username)
        group = Group.objects.get(slug=group)
        Message.objects.create(user=user, group=group, text=message)
