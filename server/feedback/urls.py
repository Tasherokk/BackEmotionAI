from django.urls import path
from .views.views_feedback import FeedbackPhotoView
from .views.views_hr import CompanyEmployeesView, HRFeedbackAnalyticsView, HREventManageView, HREventDetailView
from .views.views_employee import EmployeeEventsView



urlpatterns = [

    # Employee endpoints
    path("employee/feedback", FeedbackPhotoView.as_view()),
    path("employee/events/my", EmployeeEventsView.as_view()),
    
    # HR analytics
    path("hr/analytics/feedbacks/", HRFeedbackAnalyticsView.as_view(), name="hr-feedbacks-analytics"),
    
    
    # HR event management
    path("hr/company/employees", CompanyEmployeesView.as_view()),
    path("hr/events/", HREventManageView.as_view(), name="hr-events"),
    path("hr/events/<int:pk>/", HREventDetailView.as_view(), name="hr-event-detail"),

]
