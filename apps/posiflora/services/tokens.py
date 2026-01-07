import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from ..models import PosifloraToken


def get_token():
    token = PosifloraToken.objects.first()
    if not token:
        token = obtain_new_token()
    elif token.is_expired():
        token = refresh_token(token)
    return token


def obtain_new_token():
    response = requests.post(
        'https://floricraft.posiflora.com/api/v1/sessions',
        {
            "data": {
                "type": "sessions",
                "attributes": {
                    "username": settings.POSIFLORA_USER,
                    "password": settings.POSIFLORA_PASSWORD
                }
            }
        }
    )

    data = response.json()

    return PosifloraToken.objects.create(
        access_token=data['accessToken'],
        refresh_token=data['refreshToken'],
        expires_at=timezone.now() + timedelta(seconds=data['expireAt'])
    )
