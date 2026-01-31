from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..serializers.serializers_employee import EventSerializer
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import Event

class EmployeeEventsView(APIView):
    """Список событий для сотрудника (только события своей компании где он participant)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="List of events where user is a participant",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "starts_at": {"type": "string", "format": "date-time"},
                            "ends_at": {"type": "string", "format": "date-time"},
                            "company": {"type": "integer"},
                            "company_name": {"type": "string"},
                            "participants_count": {"type": "integer"},
                        }
                    }
                }
            ),
            403: OpenApiResponse(description="Only employees can access this endpoint"),
        },
        description="Get list of events where the authenticated employee is a participant. Only shows events from user's company.",
        summary="Get my events (Employee only)"
    )
    def get(self, request):
        from accounts.models import User
        
        # Проверяем что пользователь - сотрудник
        if request.user.role != User.Role.EMPLOYEE:
            return Response(
                {"detail": "Only employees can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Получаем события где пользователь - participant
        events = Event.objects.filter(
            company=request.user.company,
            participants=request.user
        ).select_related('company').prefetch_related('participants').order_by('-starts_at')
        
        return Response(EventSerializer(events, many=True).data)
