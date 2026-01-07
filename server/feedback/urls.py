from django.urls import path
from .views import FeedbackPhotoView
from .views_hr import HrOverviewView, HrTimelineView, HrByUserView

urlpatterns = [
    path("photo", FeedbackPhotoView.as_view()),
    path("hr/stats/overview", HrOverviewView.as_view()),
    path("hr/stats/timeline", HrTimelineView.as_view()),
    path("hr/stats/by_user", HrByUserView.as_view()),
]
