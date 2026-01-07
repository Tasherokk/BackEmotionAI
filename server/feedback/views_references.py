from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db import models

from .models import Company, Department, Event
from .serializers import CompanySerializer, DepartmentSerializer, EventSerializer


class CompaniesView(APIView):
    """Список всех компаний (для выбора при регистрации)"""
    permission_classes = [AllowAny]

    def get(self, request):
        companies = Company.objects.all().order_by('name')
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)


class DepartmentsView(APIView):
    """Список отделов (с фильтром по компании)"""
    permission_classes = [AllowAny]

    def get(self, request):
        company_id = request.query_params.get('company_id')
        
        departments = Department.objects.all()
        if company_id:
            departments = departments.filter(company_id=company_id)
        
        departments = departments.select_related('company').order_by('name')
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class EventsView(APIView):
    """Список событий"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Фильтры
        active_only = request.query_params.get('active', 'false').lower() == 'true'
        company_id = request.query_params.get('company_id')
        
        events = Event.objects.select_related('company').order_by('-starts_at')
        
        if active_only:
            from django.utils import timezone
            now = timezone.now()
            events = events.filter(starts_at__lte=now).filter(
                models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
            )
        
        if company_id:
            events = events.filter(company_id=company_id)
        
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)
