from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import IsAuthenticated
from rest_framework import status


class CompanyEmployeesView(APIView):
    """Список сотрудников компании (только для HR)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.role != 'hr':
            return Response(
                {"detail": "Only HR can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from accounts.models import User
        employees = User.objects.filter(
            company=request.user.company,
            role=User.Role.EMPLOYEE
        ).select_related('department').order_by('name')
        
        from serializers import EmployeeSerializer
        return Response(EmployeeSerializer(employees, many=True).data)
