from django.urls import path
from .views import FeedbackPhotoView

urlpatterns = [
    path("photo", FeedbackPhotoView.as_view()),
]
