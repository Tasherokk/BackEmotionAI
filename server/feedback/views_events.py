from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Event
from .serializers import EventSerializer, EventCreateSerializer
from .permissions import IsHR


class EventCRUDView(APIView):
    """CRUD для событий (только HR)"""
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request):
        """Создать событие"""
        serializer = EventCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    """Детали, редактирование и удаление события"""
    permission_classes = [IsAuthenticated, IsHR]

    def get(self, request, event_id):
        """Получить детали события"""
        try:
            event = Event.objects.select_related('company').get(id=event_id)
            return Response(EventSerializer(event).data)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, event_id):
        """Обновить событие"""
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = EventCreateSerializer(event, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(EventSerializer(event).data)

    def delete(self, request, event_id):
        """Удалить событие"""
        try:
            event = Event.objects.get(id=event_id)
            event.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
