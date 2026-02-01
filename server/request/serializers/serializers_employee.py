from rest_framework import serializers
from ..models import Request, RequestMessage, RequestType
from accounts.models import User


class HRListSerializer(serializers.ModelSerializer):
    """Список HR компании для выбора при создании заявки"""
    class Meta:
        model = User
        fields = ["id", "username", "name"]


class RequestTypeSerializer(serializers.ModelSerializer):
    """Тип заявки"""
    class Meta:
        model = RequestType
        fields = ["id", "name", "description"]


class RequestMessageSerializer(serializers.ModelSerializer):
    """Сообщение в заявке"""
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_name = serializers.CharField(source="sender.name", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = RequestMessage
        fields = ["id", "sender", "sender_username", "sender_name", "text", "file", "created_at", "is_mine"]
        read_only_fields = ["id", "sender", "created_at"]

    def get_is_mine(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return obj.sender == request.user
        return False


class RequestListSerializer(serializers.ModelSerializer):
    """Список заявок для employee"""
    type_name = serializers.CharField(source="type.name", read_only=True)
    hr_username = serializers.CharField(source="hr.username", read_only=True)
    hr_name = serializers.CharField(source="hr.name", read_only=True)
    messages_count = serializers.IntegerField(read_only=True)
    last_message_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Request
        fields = [
            "id", "type", "type_name", "hr", "hr_username", "hr_name",
            "status", "created_at", "closed_at", "messages_count", "last_message_at"
        ]


class RequestDetailSerializer(serializers.ModelSerializer):
    """Детали заявки с сообщениями"""
    type_name = serializers.CharField(source="type.name", read_only=True)
    type_description = serializers.CharField(source="type.description", read_only=True)
    hr_username = serializers.CharField(source="hr.username", read_only=True)
    hr_name = serializers.CharField(source="hr.name", read_only=True)
    messages = RequestMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Request
        fields = [
            "id", "type", "type_name", "type_description",
            "hr", "hr_username", "hr_name", "status",
            "created_at", "closed_at", "messages"
        ]


class RequestCreateSerializer(serializers.ModelSerializer):
    """Создание заявки"""
    comment = serializers.CharField(write_only=True, required=True, help_text="Initial comment (required)")

    class Meta:
        model = Request
        fields = ["type", "hr", "comment"]

    def validate_hr(self, value):
        """Проверяем что выбранный HR из той же компании что и employee"""
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("User not authenticated")
        
        if value.role != "HR":
            raise serializers.ValidationError("Selected user is not an HR")
        
        if value.company != request.user.company:
            raise serializers.ValidationError("Selected HR is not from your company")
        
        return value

    def create(self, validated_data):
        comment = validated_data.pop("comment")
        request_user = self.context.get("request").user
        
        # Создаем заявку
        request_obj = Request.objects.create(
            employee=request_user,
            **validated_data
        )
        
        # Создаем первое сообщение из комментария
        RequestMessage.objects.create(
            request=request_obj,
            sender=request_user,
            text=comment
        )
        
        return request_obj


class SendMessageSerializer(serializers.ModelSerializer):
    """Отправка сообщения в заявку"""
    class Meta:
        model = RequestMessage
        fields = ["text", "file"]

    def validate(self, attrs):
        """Проверяем что хотя бы текст или файл присутствует"""
        if not attrs.get("text") and not attrs.get("file"):
            raise serializers.ValidationError("Either text or file must be provided")
        return attrs