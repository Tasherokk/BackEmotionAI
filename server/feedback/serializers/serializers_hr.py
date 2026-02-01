from rest_framework import serializers
from accounts.models import User
from ..models import Feedback, Event


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для списка сотрудников (для HR)"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'name', 'company', 'company_name', 'department', 'department_name')


class FeedbackSerializer(serializers.ModelSerializer):
    """Сериализатор для фидбеков HR"""
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            "id",
            "user_id",
            "user_username",
            "emotion",
            "top3",
            "created_at",
            "company",
            "company_name",
            "department",
            "department_name",
            "event",
            "event_title"
        ]


class EventListSerializer(serializers.ModelSerializer):
    """Список ивентов для HR"""
    company_name = serializers.CharField(source="company.name", read_only=True)
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "starts_at",
            "ends_at",
            "company",
            "company_name",
            "participants_count"
        ]
    
    def get_participants_count(self, obj):
        return obj.participants.count()