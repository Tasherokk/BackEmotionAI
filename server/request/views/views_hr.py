from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Max
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import Request, RequestMessage
from ..permissions import IsHR, IsRequestParticipant
from ..serializers.serializers_hr import (
    RequestListSerializer, RequestDetailSerializer,
    SendMessageSerializer, UpdateStatusSerializer
)


class HRRequestListView(APIView):
    """Список заявок адресованных HR"""
    permission_classes = [IsAuthenticated, IsHR]

    @extend_schema(
        responses={200: RequestListSerializer(many=True)},
        description="Get list of all requests assigned to this HR",
        summary="Get my assigned requests (HR only)"
    )
    def get(self, request):
        requests = Request.objects.filter(
            hr=request.user
        ).select_related("type", "employee").annotate(
            messages_count=Count("messages"),
            last_message_at=Max("messages__created_at")
        )
        
        serializer = RequestListSerializer(requests, many=True)
        return Response(serializer.data)


class HRRequestDetailView(APIView):
    """Детали заявки для HR"""
    permission_classes = [IsAuthenticated, IsHR, IsRequestParticipant]

    def get_object(self, pk, user):
        obj = get_object_or_404(
            Request.objects.select_related(
                "type", "employee", "employee__department"
            ).prefetch_related("messages__sender"),
            pk=pk,
            hr=user
        )
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        responses={
            200: RequestDetailSerializer,
            404: OpenApiResponse(description="Request not found")
        },
        description="Get request details with all messages",
        summary="Get request details (HR only)"
    )
    def get(self, request, pk):
        request_obj = self.get_object(pk, request.user)
        serializer = RequestDetailSerializer(
            request_obj,
            context={"request": request}
        )
        return Response(serializer.data)


class HRRequestMessageView(APIView):
    """Отправка сообщения в заявку от HR"""
    permission_classes = [IsAuthenticated, IsHR, IsRequestParticipant]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk, user):
        obj = get_object_or_404(Request, pk=pk, hr=user)
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
        summary="Send message to request (HR only)"
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


class HRRequestStatusView(APIView):
    """Изменение статуса заявки"""
    permission_classes = [IsAuthenticated, IsHR, IsRequestParticipant]

    def get_object(self, pk, user):
        obj = get_object_or_404(Request, pk=pk, hr=user)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        request=UpdateStatusSerializer,
        responses={
            200: RequestDetailSerializer,
            400: OpenApiResponse(description="Invalid status or request already closed"),
            404: OpenApiResponse(description="Request not found")
        },
        description="Update request status to IN_PROGRESS. Cannot update closed requests.",
        summary="Update request status (HR only)"
    )
    def patch(self, request, pk):
        request_obj = self.get_object(pk, request.user)
        
        # Проверяем что заявка не закрыта
        if request_obj.status == Request.Status.CLOSED:
            return Response(
                {"detail": "Cannot update status of closed request"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = UpdateStatusSerializer(data=request.data)
        if serializer.is_valid():
            request_obj.status = serializer.validated_data["status"]
            request_obj.save(update_fields=["status"])
            
            detail_serializer = RequestDetailSerializer(
                request_obj,
                context={"request": request}
            )
            return Response(detail_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HRRequestCloseView(APIView):
    """Закрытие заявки"""
    permission_classes = [IsAuthenticated, IsHR, IsRequestParticipant]

    def get_object(self, pk, user):
        obj = get_object_or_404(Request, pk=pk, hr=user)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        responses={
            200: RequestDetailSerializer,
            400: OpenApiResponse(description="Request already closed"),
            404: OpenApiResponse(description="Request not found")
        },
        description="Close request. Only the assigned HR can close the request.",
        summary="Close request (HR only)"
    )
    def post(self, request, pk):
        request_obj = self.get_object(pk, request.user)
        
        # Проверяем что заявка еще не закрыта
        if request_obj.status == Request.Status.CLOSED:
            return Response(
                {"detail": "Request is already closed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request_obj.status = Request.Status.CLOSED
        request_obj.closed_at = timezone.now()
        request_obj.save(update_fields=["status", "closed_at"])
        
        detail_serializer = RequestDetailSerializer(
            request_obj,
            context={"request": request}
        )
        return Response(detail_serializer.data)