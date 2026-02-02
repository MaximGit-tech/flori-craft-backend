from rest_framework.authentication import BaseAuthentication
from django.core.signing import BadSignature
from .models import CustomUser

class CookieUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        try:
            user_id = request.get_signed_cookie('user_id', salt='user-auth', default=None)
        except BadSignature:
            return None

        if not user_id:
            return None

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None

        return (user, None)