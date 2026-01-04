from rest_framework.authentication import BaseAuthentication
from .models import CustomUser

class CookieUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user_id = request.COOKIES.get('user_id')
        if not user_id:
            return None

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None

        return (user, None)