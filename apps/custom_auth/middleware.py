from .models import CustomUser

class CookieUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = None
        user_id = request.COOKIES.get('user_id')
        if user_id:
            try:
                request.user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                pass
        return self.get_response(request)