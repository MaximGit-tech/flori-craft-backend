import requests
from datetime import timedelta
from django.conf import settings
from ..models import PosifloraSession


def get_session() -> PosifloraSession:
    session = PosifloraSession.objects.first()

    if not session:
        raise RuntimeError(
            'Posiflora session not initialized'
        )

    if session.is_expired():
        session = refresh_session(session)

    return session


def refresh_session(session: PosifloraSession) -> PosifloraSession:
    response = requests.patch(
        'https://floricraft.posiflora.com/api/v1/sessions',
        headers={
            'Content-Type': 'application/vnd.api+json',
            'Authorization': f'Bearer {session.access_token}',
        },
        json={
            'data': {
                'type': 'sessions',
                'attributes': {
                    'refreshToken': session.refresh_token
                }
            }
        }
    )

    response.raise_for_status()
    data = response.json()['data']['attributes']

    session.access_token = data['accessToken']
    session.refresh_token = data.get(
        'refreshToken',
        session.refresh_token
    )

    session.expires_at = data.get('expireAt') or data.get('expireAT')

    session.save()
    return session