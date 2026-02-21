from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def notify_new_message(request_id: int, message_obj):
    """Push a new message to all WebSocket clients connected to this request"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{request_id}",
        {
            "type": "chat.message",
            "data": {
                "id": message_obj.id,
                "sender": message_obj.sender.id,
                "sender_username": message_obj.sender.username,
                "sender_name": message_obj.sender.name,
                "text": message_obj.text or "",
                "file": message_obj.file.url if message_obj.file else None,
                "created_at": message_obj.created_at.isoformat(),
            },
        },
    )
