from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Max
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import Request, RequestMessage, RequestType
from ..permissions import IsEmployee, IsRequestParticipant
from ..serializers.serializers_employee import (
    HRListSerializer, RequestTypeSerializer, RequestCreateSerializer,
    RequestListSerializer, RequestDetailSerializer, SendMessageSerializer
)
from accounts.models import User


class HRListView(APIView):
    """Список HR компании для выбора при создании заявки"""
    permission_classes = [IsAuthenticated, IsEmployee]

    @extend_schema(
        responses={200: HRListSerializer(many=True)},
        description="Get list of all HR users in employee's company",
        summary="Get company HR list (Employee only)"
    )
    def get(self, request):
        hrs = User.objects.filter(
            company=request.user.company,
            role=User.Role.HR,
            is_active=True
        ).order_by("name")
        
        serializer = HRListSerializer(hrs, many=True)
        return Response(serializer.data)


class RequestTypeListView(APIView):
    """Список типов заявок"""
    permission_classes = [IsAuthenticated, IsEmployee]

    @extend_schema(
        responses={200: RequestTypeSerializer(many=True)},
        description="Get list of all available request types",
        summary="Get request types (Employee only)"
    )
    def get(self, request):
        types = RequestType.objects.all().order_by("name")
        serializer = RequestTypeSerializer(types, many=True)
        return Response(serializer.data)


class EmployeeRequestListView(APIView):
    """Список заявок employee"""
    permission_classes = [IsAuthenticated, IsEmployee]

    @extend_schema(
        responses={200: RequestListSerializer(many=True)},
        description="Get list of all requests created by the employee",
        summary="Get my requests (Employee only)"
    )
    def get(self, request):
        requests = Request.objects.filter(
            employee=request.user
        ).select_related("type", "hr").annotate(
            messages_count=Count("messages"),
            last_message_at=Max("messages__created_at")
        )
        
        serializer = RequestListSerializer(requests, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=RequestCreateSerializer,
        responses={
            201: RequestDetailSerializer,
            400: OpenApiResponse(description="Validation error")
        },
        description="Create a new request to an HR with initial comment",
        summary="Create request (Employee only)"
    )
    def post(self, request):
        serializer = RequestCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            request_obj = serializer.save()
            detail_serializer = RequestDetailSerializer(
                request_obj,
                context={"request": request}
            )
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeRequestDetailView(APIView):
    """Детали заявки для employee"""
    permission_classes = [IsAuthenticated, IsEmployee, IsRequestParticipant]

    def get_object(self, pk, user):
        obj = get_object_or_404(
            Request.objects.select_related("type", "hr").prefetch_related("messages__sender"),
            pk=pk,
            employee=user
        )
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        responses={
            200: RequestDetailSerializer,
            404: OpenApiResponse(description="Request not found")
        },
        description="Get request details with all messages",
        summary="Get request details (Employee only)"
    )
    def get(self, request, pk):
        request_obj = self.get_object(pk, request.user)
        serializer = RequestDetailSerializer(
            request_obj,
            context={"request": request}
        )
        return Response(serializer.data)


class EmployeeRequestMessageView(APIView):
    """Отправка сообщения в заявку"""
    permission_classes = [IsAuthenticated, IsEmployee, IsRequestParticipant]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk, user):
        obj = get_object_or_404(Request, pk=pk, employee=user)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        request=SendMessageSerializer,
        responses={
            201: RequestDetailSerializer,
            400: OpenApiResponse(description="Validation error or request is closed"),
            404: OpenApiResponse(description="Request not found")
        },
        description="Send a message to an existing request. Request must not be closed. You can send text, file, or both.",
        summary="Send message to request (Employee only)"
    )
    def post(self, request, pk):
        request_obj = self.get_object(pk, request.user)
        
        # Проверяем что заявка не закрыта
        if request_obj.status == Request.Status.CLOSED:
            return Response(
                {"detail": "Cannot send message to closed request"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SendMessageSerializer(data=request.data)
        if serializer.is_valid():
            RequestMessage.objects.create(
                request=request_obj,
                sender=request.user,
                **serializer.validated_data
            )
            
            # Возвращаем обновленную заявку
            detail_serializer = RequestDetailSerializer(
                request_obj,
                context={"request": request}
            )
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)