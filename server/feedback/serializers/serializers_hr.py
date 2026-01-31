from rest_framework import serializers
from accounts.models import User


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для списка сотрудников (для HR)"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'name', 'company', 'company_name', 'department', 'department_name')
