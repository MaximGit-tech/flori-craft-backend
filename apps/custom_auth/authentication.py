from rest_framework.authentication import BaseAuthentication
from django.core.signing import Signer, BadSignature
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

class CookieUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw_cookie = request.COOKIES.get('user_id')
        if not raw_cookie:
            logger.info("No user_id cookie found")
            return None

        try:
            signer = Signer(salt='user-auth')
            user_id = signer.unsign(raw_cookie)
            logger.info(f"Signed cookie user_id: {user_id}")
        except BadSignature:
            logger.warning("BadSignature: cookie was tampered or invalid")
            return None

        try:
            user = CustomUser.objects.get(id=user_id)
            logger.info(f"User authenticated: {user.id}")
        except CustomUser.DoesNotExist:
            logger.warning(f"User {user_id} not found in database")
            return None

        return (user, None)