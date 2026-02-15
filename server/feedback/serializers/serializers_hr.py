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


class EventDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор ивента с ID участников"""
    company_name = serializers.CharField(source="company.name", read_only=True)
    participants = serializers.SerializerMethodField()
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
            "participants",
            "participants_count",
        ]

    def get_participants(self, obj):
        return list(obj.participants.values_list("id", flat=True))

    def get_participants_count(self, obj):
        return obj.participants.count()


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и обновление ивента"""
    participants = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    starts_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S%z",
        input_formats=["iso-8601", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M"],
        help_text="Дата и время начала в формате ISO 8601, например: 2026-02-15T10:00:00Z",
    )
    ends_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S%z",
        input_formats=["iso-8601", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M"],
        help_text="Дата и время окончания в формате ISO 8601, например: 2026-02-15T12:00:00Z",
    )
    
    class Meta:
        model = Event
        fields = ["title", "starts_at", "ends_at", "participants"]
    
    def validate_participants(self, participant_ids):
        """Проверяем что все участники существуют и являются Employee компании HR"""
        if not participant_ids:
            return []
        
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("User not authenticated")
        
        # Проверяем существование пользователей
        existing_users = User.objects.filter(id__in=participant_ids)
        existing_ids = set(existing_users.values_list('id', flat=True))
        
        for pid in participant_ids:
            if pid not in existing_ids:
                raise serializers.ValidationError(
                    f'User with ID {pid} does not exist'
                )
        
        # Проверяем что все из нашей компании и Employee
        for user in existing_users:
            if user.company_id != request.user.company_id:
                raise serializers.ValidationError(
                    f'User "{user.username}" (ID: {user.id}) is not from your company'
                )
            if user.role != User.Role.EMPLOYEE:
                raise serializers.ValidationError(
                    f'User "{user.username}" (ID: {user.id}) is not an employee'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    f'User "{user.username}" (ID: {user.id}) is not active'
                )
        
        # Возвращаем объекты User для дальнейшего использования
        return list(existing_users)
    
    def validate(self, attrs):
        """Валидация дат"""
        from django.utils import timezone
        import zoneinfo
        
        almaty_tz = zoneinfo.ZoneInfo("Asia/Almaty")
        
        starts_at = attrs.get("starts_at", self.instance.starts_at if self.instance else None)
        ends_at = attrs.get("ends_at", self.instance.ends_at if self.instance else None)
        
        # Проверяем что ends_at позже starts_at
        if ends_at and starts_at and ends_at <= starts_at:
            raise serializers.ValidationError({
                "ends_at": "End date must be after start date"
            })
        
        # Проверяем что starts_at не в прошлом по времени Алматы (только при создании)
        if not self.instance and starts_at:
            now_almaty = timezone.now().astimezone(almaty_tz)
            starts_at_almaty = starts_at.astimezone(almaty_tz)
            if starts_at_almaty < now_almaty:
                raise serializers.ValidationError({
                    "starts_at": "Start date cannot be in the past"
                })
        
        return attrs
    
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