from rest_framework.authentication import BaseAuthentication
from django.core.signing import BadSignature
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

class CookieUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        try:
            user_id = request.get_signed_cookie('user_id', salt='user-auth', default=None)
            logger.info(f"Signed cookie user_id: {user_id}")
        except BadSignature as e:
            logger.warning(f"BadSignature: cookie was tampered or old unsigned cookie")
            return None

        if not user_id:
            logger.info("No user_id cookie found")
            return None

        try:
            user = CustomUser.objects.get(id=user_id)
            logger.info(f"User authenticated: {user.id}")
        except CustomUser.DoesNotExist:
            logger.warning(f"User {user_id} not found in database")
            return None

        return (user, None)