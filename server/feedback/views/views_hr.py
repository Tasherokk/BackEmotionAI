from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from ..permissions import IsHR
from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import datetime


class CompanyEmployeesView(APIView):
    """Список сотрудников компании (только для HR)"""
    permission_classes = [IsAuthenticated, IsHR]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="List of company employees",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"},
                            "name": {"type": "string"},
                            "company": {"type": "integer"},
                            "company_name": {"type": "string"},
                            "department": {"type": "integer"},
                            "department_name": {"type": "string"},
                        }
                    }
                }
            ),
            403: OpenApiResponse(description="Only HR can access this endpoint"),
        },
        description="Get list of all employees in HR's company. Only accessible by HR users.",
        summary="Get company employees (HR only)"
    )
    def get(self, request):
        from accounts.models import User

        employees = User.objects.filter(
            company=request.user.company,
            role=User.Role.EMPLOYEE
        ).select_related('department').order_by('name')
        
        from ..serializers.serializers_hr import EmployeeSerializer
        return Response(EmployeeSerializer(employees, many=True).data)



class HRFeedbackAnalyticsView(APIView):
    """Получение фидбеков с фильтрами для аналитики"""
    permission_classes = [IsAuthenticated, IsHR]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Start date (YYYY-MM-DD)",
                required=True
            ),
            OpenApiParameter(
                name="end_date",
                type=str,
                location=OpenApiParameter.QUERY,
                description="End date (YYYY-MM-DD)",
                required=True
            ),
            OpenApiParameter(
                name="emotions",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated emotions (e.g., happy,sad,angry)",
                required=False
            ),
            OpenApiParameter(
                name="departments",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated department IDs (e.g., 1,2,3)",
                required=False
            ),
            OpenApiParameter(
                name="event_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Specific event ID",
                required=False
            ),
            OpenApiParameter(
                name="has_event",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by event presence (true/false)",
                required=False
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of feedbacks matching the filters",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "user_id": {"type": "integer"},
                            "user_username": {"type": "string"},
                            "emotion": {"type": "string"},
                            "top3": {"type": "object"},
                            "created_at": {"type": "string", "format": "date-time"},
                            "company": {"type": "integer"},
                            "company_name": {"type": "string"},
                            "department": {"type": "integer"},
                            "department_name": {"type": "string"},
                            "event": {"type": "integer", "nullable": True},
                            "event_title": {"type": "string", "nullable": True},
                        }
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid parameters"),
            403: OpenApiResponse(description="Only HR can access this endpoint"),
        },
        description="Get filtered feedbacks for analytics. Date range is required. All feedbacks are from HR's company only. Returns oldest first.",
        summary="Get feedbacks with filters (HR only)"
    )
    def get(self, request):
        from ..models import Feedback
        
        # Проверка обязательных параметров
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        
        if not start_date_str or not end_date_str:
            return Response(
                {"detail": "start_date and end_date are required (format: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Парсинг дат
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            # Устанавливаем время для полного дня
            from django.utils import timezone
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Базовый queryset - только фидбеки компании HR
        feedbacks = Feedback.objects.filter(
            company=request.user.company,
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        # Фильтр по эмоциям
        emotions_str = request.query_params.get("emotions")
        if emotions_str:
            emotions_list = [e.strip() for e in emotions_str.split(",") if e.strip()]
            if emotions_list:
                feedbacks = feedbacks.filter(emotion__in=emotions_list)
        
        # Фильтр по департаментам
        departments_str = request.query_params.get("departments")
        if departments_str:
            try:
                department_ids = [int(d.strip()) for d in departments_str.split(",") if d.strip()]
                if department_ids:
                    feedbacks = feedbacks.filter(department_id__in=department_ids)
            except ValueError:
                return Response(
                    {"detail": "Invalid department IDs format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Фильтр по конкретному ивенту
        event_id = request.query_params.get("event_id")
        if event_id:
            try:
                feedbacks = feedbacks.filter(event_id=int(event_id))
            except ValueError:
                return Response(
                    {"detail": "Invalid event_id format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Фильтр по наличию ивента
        has_event = request.query_params.get("has_event")
        if has_event:
            if has_event.lower() == "true":
                feedbacks = feedbacks.filter(event__isnull=False)
            elif has_event.lower() == "false":
                feedbacks = feedbacks.filter(event__isnull=True)
        
        # Сортировка: старые первые
        feedbacks = feedbacks.select_related(
            "user", "company", "department", "event"
        ).order_by("created_at")
        
        from ..serializers.serializers_hr import FeedbackSerializer
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)


class HREventManageView(APIView):
    """Создание и список ивентов компании"""
    permission_classes = [IsAuthenticated, IsHR]

    @extend_schema(
        responses={
            200: {
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
                        "participants_count": {"type": "integer"}
                    }
                }
            },
            403: OpenApiResponse(description="Only HR can access this endpoint"),
        },
        description="Get list of all events in HR's company",
        summary="Get company events (HR only)"
    )
    def get(self, request):
        """Список всех ивентов компании"""
        from ..models import Event
        
        events = Event.objects.filter(
            company=request.user.company
        ).select_related("company").prefetch_related("participants").order_by("-starts_at")
        
        from ..serializers.serializers_hr import EventListSerializer
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

    @extend_schema(
        request={"application/json": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "example": "Team Meeting"},
                "starts_at": {"type": "string", "format": "date-time", "example": "2026-02-15T10:00:00Z"},
                "ends_at": {"type": "string", "format": "date-time", "example": "2026-02-15T12:00:00Z"},
                "participants": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Array of employee IDs (optional)",
                    "example": [1, 2, 3]
                }
            },
            "required": ["title", "starts_at", "ends_at"]
        }},
        responses={
            201: OpenApiResponse(description="Event created successfully"),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Only HR can access this endpoint"),
        },
        description="Create a new event in HR's company. Start date must be in the future. End date must be after start date. Participants must be employees from the same company.",
        summary="Create event (HR only)"
    )
    def post(self, request):
        """Создание нового ивента"""
        from ..serializers.serializers_hr import EventCreateUpdateSerializer
        
        serializer = EventCreateUpdateSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            event = serializer.save()
            
            # Возвращаем созданный ивент
            from ..serializers.serializers_hr import EventListSerializer
            response_serializer = EventListSerializer(event)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HREventDetailView(APIView):
    """Редактирование и удаление ивента"""
    permission_classes = [IsAuthenticated, IsHR]

    def get_object(self, pk, user):
        """Получаем ивент только своей компании"""
        from ..models import Event
        obj = get_object_or_404(Event, pk=pk, company=user.company)
        return obj

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Event details with participant IDs"),
            403: OpenApiResponse(description="Only HR can access this endpoint"),
            404: OpenApiResponse(description="Event not found"),
        },
        description="Get detailed event info including all fields and participant IDs. Only events from HR's company.",
        summary="Get event detail (HR only)"
    )
    def get(self, request, pk):
        """Получение детальной информации об ивенте"""
        event = self.get_object(pk, request.user)
        from ..serializers.serializers_hr import EventDetailSerializer
        serializer = EventDetailSerializer(event)
        return Response(serializer.data)

    @extend_schema(
        request={"application/json": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "example": "Updated Team Meeting"},
                "starts_at": {"type": "string", "format": "date-time", "example": "2026-02-15T10:00:00Z"},
                "ends_at": {"type": "string", "format": "date-time", "example": "2026-02-15T12:00:00Z"},
                "participants": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Array of employee IDs",
                    "example": [1, 2, 3, 4]
                }
            }
        }},
        responses={
            200: OpenApiResponse(description="Event updated successfully"),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Only HR can access this endpoint"),
            404: OpenApiResponse(description="Event not found"),
        },
        description="Partially update an event. Can only update events from HR's company. All fields are optional - only provided fields will be updated. All validations apply (dates, participants).",
        summary="Update event (HR only)"
    )
    def put(self, request, pk):
        """Частичное обновление ивента"""
        event = self.get_object(pk, request.user)
        
        from ..serializers.serializers_hr import EventCreateUpdateSerializer
        serializer = EventCreateUpdateSerializer(
            event,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        if serializer.is_valid():
            updated_event = serializer.save()
            
            # Возвращаем обновленный ивент
            from ..serializers.serializers_hr import EventListSerializer
            response_serializer = EventListSerializer(updated_event)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Event deleted successfully"),
            403: OpenApiResponse(description="Only HR can access this endpoint"),
            404: OpenApiResponse(description="Event not found"),
        },
        description="Delete an event from HR's company. Feedbacks linked to this event will have event field set to null.",
        summary="Delete event (HR only)"
    )
    def delete(self, request, pk):
        """Удаление ивента"""
        event = self.get_object(pk, request.user)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)