from rest_framework import serializers
from .models import Company, Department, Event, Feedback


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name')


class DepartmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Department
        fields = ('id', 'name', 'company', 'company_name')


class EventSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    participants_count = serializers.IntegerField(source='participants.count', read_only=True)
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'starts_at', 'ends_at', 'company', 'company_name', 'participants_count')


class EventCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        write_only=True
    )
    
    class Meta:
        model = Event
        fields = ('title', 'starts_at', 'ends_at', 'company', 'participant_ids')
    
    def validate_company(self, value):
        """Проверка, что HR может создавать события только для своей компании"""
        user = self.context['request'].user
        if user.company and value != user.company:
            raise serializers.ValidationError("You can only create events for your company")
        return value
    
    def validate(self, attrs):
        """Проверка, что участники принадлежат компании события"""
        participant_ids = attrs.get('participant_ids', [])
        company = attrs.get('company')
        
        if participant_ids and company:
            from accounts.models import User
            # Проверяем что все участники - сотрудники этой компании
            invalid_users = User.objects.filter(
                id__in=participant_ids
            ).exclude(
                company=company,
                role=User.Role.EMPLOYEE
            ).values_list('id', flat=True)
            
            if invalid_users:
                raise serializers.ValidationError({
                    "participant_ids": f"Users {list(invalid_users)} are not employees of this company"
                })
        
        return attrs
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        event = Event.objects.create(**validated_data)
        
        if participant_ids:
            from accounts.models import User
            participants = User.objects.filter(
                id__in=participant_ids,
                company=event.company,
                role=User.Role.EMPLOYEE
            )
            event.participants.set(participants)
        
        return event


class FeedbackSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Feedback
        fields = (
            'id', 'created_at', 'emotion', 'confidence', 
            'top3', 'face_box', 'probs',
            'event', 'event_title',
            'company', 'company_name',
            'department', 'department_name'
        )


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
