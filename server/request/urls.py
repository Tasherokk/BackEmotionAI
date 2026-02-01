from django.urls import path
from .views.views_employee import (
    HRListView, RequestTypeListView, EmployeeRequestListView,
    EmployeeRequestDetailView, EmployeeRequestMessageView
)
from .views.views_hr import (
    HRRequestListView, HRRequestDetailView, HRRequestMessageView,
    HRRequestStatusView, HRRequestCloseView
)


urlpatterns = [
    # Employee endpoints
    path("employee/requests/hr-list/", HRListView.as_view(), name="employee-hr-list"),
    path("employee/requests/types/", RequestTypeListView.as_view(), name="employee-request-types"),
    path("employee/requests/", EmployeeRequestListView.as_view(), name="employee-requests"),
    path("employee/requests/<int:pk>/", EmployeeRequestDetailView.as_view(), name="employee-request-detail"),
    path("employee/requests/<int:pk>/messages/", EmployeeRequestMessageView.as_view(), name="employee-request-message"),
    
    # HR endpoints
    path("hr/requests/", HRRequestListView.as_view(), name="hr-requests"),
    path("hr/requests/<int:pk>/", HRRequestDetailView.as_view(), name="hr-request-detail"),
    path("hr/requests/<int:pk>/messages/", HRRequestMessageView.as_view(), name="hr-request-message"),
    path("hr/requests/<int:pk>/status/", HRRequestStatusView.as_view(), name="hr-request-status"),
    path("hr/requests/<int:pk>/close/", HRRequestCloseView.as_view(), name="hr-request-close"),
]