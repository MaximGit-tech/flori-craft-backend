from django.core.signing import BadSignature
from .models import CustomUser

class CookieUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = None
        try:
            user_id = request.get_signed_cookie('user_id', salt='user-auth', default=None)
            if user_id:
                request.user = CustomUser.objects.get(id=user_id)
        except (BadSignature, CustomUser.DoesNotExist):
            pass
        return self.get_response(request)