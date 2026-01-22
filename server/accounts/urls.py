from django.urls import path
from .views import RegisterView, LoginView, RefreshView, MeView, PhotoLoginView

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
    path("refresh", RefreshView.as_view()),
    path("photo-login", PhotoLoginView.as_view()),
    path("me", MeView.as_view()),
]
