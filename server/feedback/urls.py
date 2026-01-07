from django.urls import path
from .views import FeedbackPhotoView
from .views_hr import HrOverviewView, HrTimelineView, HrByUserView
from .views_employee import MyFeedbackView, MyStatsView
from .views_events import EventCRUDView, EventDetailView
from .views_references import CompaniesView, DepartmentsView, EventsView

urlpatterns = [
    # Справочники
    path("companies", CompaniesView.as_view()),
    path("departments", DepartmentsView.as_view()),
    path("events", EventsView.as_view()),
    
    # Employee endpoints
    path("photo", FeedbackPhotoView.as_view()),
    path("my", MyFeedbackView.as_view()),
    path("my/stats", MyStatsView.as_view()),
    
    # HR analytics
    path("hr/stats/overview", HrOverviewView.as_view()),
    path("hr/stats/timeline", HrTimelineView.as_view()),
    path("hr/stats/by_user", HrByUserView.as_view()),
    
    # HR event management
    path("hr/events", EventCRUDView.as_view()),
    path("hr/events/<int:event_id>", EventDetailView.as_view()),
]
