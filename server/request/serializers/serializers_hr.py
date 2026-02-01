from rest_framework import serializers
from ..models import Request, RequestMessage


class RequestMessageSerializer(serializers.ModelSerializer):
    """Сообщение в заявке для HR"""
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
    """Список заявок для HR"""
    type_name = serializers.CharField(source="type.name", read_only=True)
    employee_username = serializers.CharField(source="employee.username", read_only=True)
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    messages_count = serializers.IntegerField(read_only=True)
    last_message_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Request
        fields = [
            "id", "type", "type_name", "employee", "employee_username", "employee_name",
            "status", "created_at", "closed_at", "messages_count", "last_message_at"
        ]


class RequestDetailSerializer(serializers.ModelSerializer):
    """Детали заявки с сообщениями для HR"""
    type_name = serializers.CharField(source="type.name", read_only=True)
    type_description = serializers.CharField(source="type.description", read_only=True)
    employee_username = serializers.CharField(source="employee.username", read_only=True)
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    employee_department = serializers.CharField(source="employee.department.name", read_only=True)
    messages = RequestMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Request
        fields = [
            "id", "type", "type_name", "type_description",
            "employee", "employee_username", "employee_name", "employee_department",
            "status", "created_at", "closed_at", "messages"
        ]


class SendMessageSerializer(serializers.ModelSerializer):
    """Отправка сообщения в заявку для HR"""
    class Meta:
        model = RequestMessage
        fields = ["text", "file"]

    def validate(self, attrs):
        """Проверяем что хотя бы текст или файл присутствует"""
        if not attrs.get("text") and not attrs.get("file"):
            raise serializers.ValidationError("Either text or file must be provided")
        return attrs


class UpdateStatusSerializer(serializers.Serializer):
    """Изменение статуса заявки"""
    status = serializers.ChoiceField(choices=["IN_PROGRESS"])