import logging
import sys
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class PosifloraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.posiflora'
    verbose_name = 'Posiflora Integration'

    def ready(self):
        """Автоматическая инициализация Posiflora сессии при старте Django"""
        if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'test', 'check']):
            return

        from .models import PosifloraSession
        from .services.tokens import refresh_session
        import requests
        from datetime import datetime, timedelta
        from django.utils import timezone

        try:
            username = getattr(settings, 'POSIFLORA_USER', None)
            password = getattr(settings, 'POSIFLORA_PASSWORD', None)

            if not username or not password:
                logger.warning(
                    'Posiflora credentials not configured. '
                    'Set POSIFLORA_USER and POSIFLORA_PASSWORD in settings.'
                )
                return

            session = PosifloraSession.objects.first()

            if session:
                if not session.is_expired():
                    logger.info('Posiflora session is active')
                    return

                try:
                    refresh_session(session)
                    logger.info('Posiflora session refreshed successfully')
                    return
                except Exception as e:
                    logger.warning(f'Failed to refresh session: {e}. Creating new session...')
                    session.delete()

            base_url = getattr(
                settings,
                'POSIFLORA_URL',
                'https://floricraft.posiflora.com/api/v1'
            )
            sessions_url = f"{base_url}/sessions"

            logger.info(f'Initializing new Posiflora session: {sessions_url}')

            response = requests.post(
                sessions_url,
                headers={
                    'Content-Type': 'application/vnd.api+json',
                    'Accept': 'application/vnd.api+json',
                },
                json={
                    'data': {
                        'type': 'sessions',
                        'attributes': {
                            'username': username,
                            'password': password,
                        }
                    }
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()
            attributes = data.get('data', {}).get('attributes', {})

            access_token = attributes.get('accessToken')
            refresh_token = attributes.get('refreshToken')
            expire_at = attributes.get('expireAt') or attributes.get('expireAT')

            if not access_token or not refresh_token:
                logger.error('Invalid response from Posiflora API (missing tokens)')
                return

            if expire_at:
                if isinstance(expire_at, str):
                    try:
                        expires_at = datetime.fromisoformat(expire_at)
                        if expires_at.tzinfo is None:
                            expires_at = timezone.make_aware(expires_at, timezone.utc)
                    except (ValueError, AttributeError):
                        expires_at = timezone.now() + timedelta(hours=24)
                else:
                    expires_at = timezone.now() + timedelta(hours=24)
            else:
                expires_at = timezone.now() + timedelta(hours=24)

            PosifloraSession.objects.create(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

            logger.info('Posiflora session initialized successfully')

        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to initialize Posiflora session: {e}')
        except Exception as e:
            logger.error(f'Unexpected error during Posiflora initialization: {e}')
