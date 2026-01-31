from rest_framework import serializers
from ..models import Event


class EventSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    participants_count = serializers.IntegerField(source='participants.count', read_only=True)
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'starts_at', 'ends_at', 'company', 'company_name', 'participants_count')

