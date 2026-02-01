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


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и обновление ивента"""
    participants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),
        many=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Event
        fields = ["title", "starts_at", "ends_at", "participants"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user:
            # Только Employee своей компании
            self.fields["participants"].queryset = User.objects.filter(
                company=request.user.company,
                role=User.Role.EMPLOYEE,
                is_active=True
            )
    
    def validate(self, attrs):
        """Валидация дат"""
        from django.utils import timezone
        
        starts_at = attrs.get("starts_at")
        ends_at = attrs.get("ends_at")
        
        # Проверяем что ends_at позже starts_at
        if ends_at and starts_at and ends_at <= starts_at:
            raise serializers.ValidationError({
                "ends_at": "End date must be after start date"
            })
        
        # Проверяем что starts_at не в прошлом
        if starts_at and starts_at < timezone.now():
            raise serializers.ValidationError({
                "starts_at": "Start date cannot be in the past"
            })
        
        return attrs
    
    def validate_participants(self, value):
        """Проверяем что все участники - Employee компании HR"""
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("User not authenticated")
        
        for user in value:
            if user.company != request.user.company:
                raise serializers.ValidationError(
                    f"User {user.username} is not from your company"
                )
            if user.role != User.Role.EMPLOYEE:
                raise serializers.ValidationError(
                    f"User {user.username} is not an employee"
                )
        
        return value
    
    def create(self, validated_data):
        """Создание ивента"""
        participants = validated_data.pop("participants", [])
        request = self.context.get("request")
        
        # Создаем ивент с company от HR
        event = Event.objects.create(
            company=request.user.company,
            **validated_data
        )
        
        # Добавляем участников
        if participants:
            event.participants.set(participants)
        
        return event
    
    def update(self, instance, validated_data):
        """Обновление ивента"""
        participants = validated_data.pop("participants", None)
        
        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем участников если переданы
        if participants is not None:
            instance.participants.set(participants)
        
        return instance