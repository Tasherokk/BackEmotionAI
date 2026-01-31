from rest_framework import serializers
from ..models import Event

class FeedbackPhotoRequestSerializer(serializers.Serializer):
    file = serializers.ImageField()
    event_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Проверка существования события и что пользователь - участник"""
        event_id = attrs.get('event_id')
        
        # Пропускаем проверку если event_id не передан или равен 0
        if not event_id or event_id == 0:
            return attrs
        
        # Проверяем существование события и участие пользователя за один запрос
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError({"event_id": "Authentication required"})
        
        event = Event.objects.filter(id=event_id).first()
        
        if not event:
            raise serializers.ValidationError({
                "event_id": f"Event with id {event_id} does not exist"
            })
        
        if not event.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError({
                "event_id": "You are not a participant of this event"
            })
        
        return attrs