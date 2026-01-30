import requests
import time
import logging
from datetime import timedelta
from django.conf import settings
from ..models import PosifloraSession

logger = logging.getLogger(__name__)


def create_new_session() -> PosifloraSession:
    """
    Создать новую сессию Posiflora через API

    Returns:
        Новая сессия

    Raises:
        RuntimeError: Если не удалось создать сессию
    """
    from django.conf import settings
    from datetime import datetime, timedelta
    from django.utils import timezone

    username = getattr(settings, 'POSIFLORA_USER', None)
    password = getattr(settings, 'POSIFLORA_PASSWORD', None)

    if not username or not password:
        raise RuntimeError(
            'Posiflora credentials not configured. '
            'Set POSIFLORA_USER and POSIFLORA_PASSWORD in settings.'
        )

    base_url = getattr(
        settings,
        'POSIFLORA_URL',
        'https://floricraft.posiflora.com/api/v1'
    )
    sessions_url = f"{base_url}/sessions"

    logger.info('Creating new Posiflora session...')

    try:
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
            raise RuntimeError('Invalid response from Posiflora API (missing tokens)')

        if expire_at and isinstance(expire_at, str):
            try:
                expires_at = datetime.fromisoformat(expire_at)
                if expires_at.tzinfo is None:
                    expires_at = timezone.make_aware(expires_at, timezone.utc)
            except (ValueError, AttributeError):
                expires_at = timezone.now() + timedelta(hours=24)
        else:
            expires_at = timezone.now() + timedelta(hours=24)

        PosifloraSession.objects.all().delete()

        session = PosifloraSession.objects.create(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        logger.info('New Posiflora session created successfully')
        return session

    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to create Posiflora session: {e}')
        raise RuntimeError(f'Failed to create Posiflora session: {e}') from e


def get_session(force_refresh: bool = False) -> PosifloraSession:
    """
    Получить актуальную сессию Posiflora с автоматическим созданием при необходимости

    Args:
        force_refresh: Принудительно обновить сессию, даже если не истекла

    Returns:
        Актуальная сессия

    Raises:
        RuntimeError: Если не удалось получить/создать сессию
    """
    session = PosifloraSession.objects.first()

    if not session:
        logger.info('No Posiflora session found, creating new one...')
        return create_new_session()

    if force_refresh or session.is_expired():
        try:
            session = refresh_session(session)
        except RuntimeError as e:
            if 'Refresh token истек' in str(e):
                logger.warning('Refresh token expired, creating new session...')
                return create_new_session()
            raise

    return session


def make_request_with_retry(
    method: str,
    url: str,
    headers: dict = None,
    **kwargs
) -> requests.Response:
    """
    Выполнить HTTP-запрос с автоматическим refresh токена при 401 ошибке

    Args:
        method: HTTP метод (GET, POST, etc.)
        url: URL для запроса
        headers: Заголовки запроса
        **kwargs: Дополнительные параметры для requests

    Returns:
        Response объект

    Raises:
        RuntimeError: Если запрос провалился после retry
    """
    session = get_session()

    if headers is None:
        headers = {}
    headers['Authorization'] = f'Bearer {session.access_token}'

    response = requests.request(method, url, headers=headers, **kwargs)

    if response.status_code == 401:
        logger.info('Токен истек во время запроса, обновляем сессию...')

        session = get_session(force_refresh=True)
        headers['Authorization'] = f'Bearer {session.access_token}'

        response = requests.request(method, url, headers=headers, **kwargs)

    response.raise_for_status()
    return response


def refresh_session(session: PosifloraSession, max_retries: int = 3) -> PosifloraSession:
    """
    Обновить сессию Posiflora с retry логикой

    Args:
        session: Текущая сессия для обновления
        max_retries: Максимальное количество попыток (по умолчанию 3)

    Returns:
        Обновленная сессия

    Raises:
        RuntimeError: Если все попытки обновления провалились
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
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
                },
                timeout=10
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

            if attempt > 0:
                logger.info(f'Сессия успешно обновлена после {attempt + 1} попытки')

            return session

        except requests.exceptions.HTTPError as e:
            last_exception = e

            if e.response.status_code in (401, 403):
                logger.error(f'Refresh token истек или невалиден (статус {e.response.status_code})')
                raise RuntimeError(
                    'Refresh token истек. Необходимо создать новую сессию через '
                    'python manage.py init_posiflora_session'
                ) from e

            logger.warning(
                f'Ошибка обновления сессии (попытка {attempt + 1}/{max_retries}): '
                f'{e.response.status_code} - {e.response.text}'
            )

        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(
                f'Ошибка сети при обновлении сессии (попытка {attempt + 1}/{max_retries}): {e}'
            )

        if attempt < max_retries - 1:
            delay = 2 ** attempt 
            logger.info(f'Повтор через {delay} секунд...')
            time.sleep(delay)

    logger.error(f'Не удалось обновить сессию после {max_retries} попыток')
    raise RuntimeError(
        f'Не удалось обновить сессию Posiflora после {max_retries} попыток'
    ) from last_exception