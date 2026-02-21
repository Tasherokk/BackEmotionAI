from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings


def _absolute_file_url(file_field):
    """Build full URL for a file field so mobile clients can open it directly"""
    if not file_field:
        return None
    url = file_field.url  # e.g. /media/request_files/doc.pdf
    base = settings.BASE_BACKEND_URL  # e.g. http://185.5.206.121
    return f"{base}{url}"


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
                "file": _absolute_file_url(message_obj.file),
                "created_at": message_obj.created_at.isoformat(),
            },
        },
    )
