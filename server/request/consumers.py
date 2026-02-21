from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for chat by request_id.
    Client connects to ws/chat/<request_id>/?token=<jwt_access>
    """

    async def connect(self):
        self.request_id = self.scope["url_route"]["kwargs"]["request_id"]
        self.room_group = f"chat_{self.request_id}"
        user = self.scope.get("user", AnonymousUser())

        if isinstance(user, AnonymousUser) or not await self._is_participant(user):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        pass  # messages are sent via REST, not WS

    async def chat_message(self, event):
        """Receive from channel_layer and send to WebSocket client"""
        await self.send_json(event["data"])

    @database_sync_to_async
    def _is_participant(self, user):
        from request.models import Request
        return Request.objects.filter(
            Q(employee=user) | Q(hr=user),
            pk=self.request_id,
        ).exists()
