from rest_framework.permissions import BasePermission

class IsHR(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", None) == "HR")


class IsEmployee(BasePermission):
    """Проверяет что пользователь - Employee"""
    def has_permission(self, request, view):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and getattr(request.user, "role", None) == "EMPLOYEE"
        )
    

class IsRequestParticipant(BasePermission):
    """Проверяет что пользователь - участник заявки (employee или hr)"""
    def has_object_permission(self, request, view, obj):
        return obj.employee == request.user or obj.hr == request.user