from django.urls import path
from .views.views_feedback import FeedbackPhotoView
from .views.views_hr import CompanyEmployeesView
from .views.views_employee import EmployeeEventsView



urlpatterns = [

    # Employee endpoints
    path("photo", FeedbackPhotoView.as_view()),
    path("employee/events/my", EmployeeEventsView.as_view()),
    
    # HR analytics
    
    
    # HR event management
    path("hr/company/employees", CompanyEmployeesView.as_view()),

]
