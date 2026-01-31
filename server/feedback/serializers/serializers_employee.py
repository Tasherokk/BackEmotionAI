from rest_framework import serializers
from ..models import Event, Feedback


class EventSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    participants_count = serializers.IntegerField(source='participants.count', read_only=True)
    has_feedback = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'starts_at', 'ends_at', 'company', 'company_name', 'participants_count', 'has_feedback')
    
    def get_has_feedback(self, obj):
        """Проверяет оставлял ли текущий пользователь feedback на это событие"""
        request = self.context.get('request')
        if request and request.user:
            return Feedback.objects.filter(event=obj, user=request.user).exists()
        return False

