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
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'starts_at', 'ends_at', 'company', 'company_name')


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('title', 'starts_at', 'ends_at', 'company')
    
    def validate_company(self, value):
        """Проверка, что HR может создавать события только для своей компании"""
        user = self.context['request'].user
        if user.company and value != user.company:
            raise serializers.ValidationError("You can only create events for your company")
        return value


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
