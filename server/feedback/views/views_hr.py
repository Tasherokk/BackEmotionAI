from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..permissions import IsHR


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
