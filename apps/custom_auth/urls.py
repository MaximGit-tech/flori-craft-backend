from django.urls import path
from .views import SendSmsView, VerifySmsRegisterView, ProfileView, VerifySmsLoginView, CheckPhoneView

urlpatterns = [
    path("send_sms/", SendSmsView.as_view()),
    path("verify_register/", VerifySmsRegisterView.as_view()),
    path("verify_login/", VerifySmsLoginView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("check_phone/", CheckPhoneView.as_view())
]