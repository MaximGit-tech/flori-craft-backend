from django.urls import path
from .views import SendSmsView, VerifySmsView, LogoutView, ProfileView

urlpatterns = [
    path("send-sms/", SendSmsView.as_view()),
    path("verify/", VerifySmsView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("profile/", ProfileView.as_view())
]