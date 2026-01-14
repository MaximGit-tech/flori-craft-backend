import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from apps.posiflora.models import PosifloraSession


class Command(BaseCommand):
    help = 'Инициализация сессии Posiflora API (получение токенов доступа)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Имя пользователя Posiflora (если не указано, берется из settings.POSIFLORA_USER)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Пароль Posiflora (если не указан, берется из settings.POSIFLORA_PASSWORD)',
        )
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help='URL Posiflora API (по умолчанию из settings.POSIFLORA_URL или https://floricraft.posiflora.com/api/v1)',
        )

    def handle(self, *args, **options):
        # Получаем учетные данные
        username = options.get('username') or getattr(settings, 'POSIFLORA_USER', None)
        password = options.get('password') or getattr(settings, 'POSIFLORA_PASSWORD', None)

        if not username or not password:
            raise CommandError(
                'Необходимо указать username и password либо через параметры команды, '
                'либо через переменные окружения POSIFLORA_USER и POSIFLORA_PASSWORD'
            )

        # Получаем URL API
        base_url = options.get('url') or getattr(
            settings,
            'POSIFLORA_URL',
            'https://floricraft.posiflora.com/api/v1'
        )
        sessions_url = f"{base_url}/sessions"

        self.stdout.write(self.style.WARNING(f'Подключение к Posiflora API: {sessions_url}'))
        self.stdout.write(f'Username: {username}')

        try:
            # Делаем запрос на получение токенов
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
                }
            )

            # Проверяем статус ответа
            response.raise_for_status()
            data = response.json()

            # Извлекаем данные из ответа
            attributes = data.get('data', {}).get('attributes', {})

            access_token = attributes.get('accessToken')
            refresh_token = attributes.get('refreshToken')
            expire_at = attributes.get('expireAt') or attributes.get('expireAT')

            if not access_token or not refresh_token:
                raise CommandError('API вернул некорректные данные (отсутствуют токены)')

            # Парсим expires_at
            if expire_at:
                if isinstance(expire_at, str):
                    try:
                        # Используем fromisoformat для парсинга ISO 8601 формата
                        # Формат: "2026-01-12T19:39:42+00:00"
                        expires_at = datetime.fromisoformat(expire_at)

                        # Если timezone не указан, добавляем UTC
                        if expires_at.tzinfo is None:
                            expires_at = timezone.make_aware(expires_at, timezone.utc)

                    except (ValueError, AttributeError) as e:
                        self.stdout.write(self.style.WARNING(
                            f'Не удалось распарсить expireAt: {expire_at}, ошибка: {e}\n'
                            'Используется значение по умолчанию (24 часа)'
                        ))
                        expires_at = timezone.now() + timedelta(hours=24)
                else:
                    expires_at = timezone.now() + timedelta(hours=24)
            else:
                # Если expire_at не указан, используем 24 часа по умолчанию
                expires_at = timezone.now() + timedelta(hours=24)

            # Удаляем старые сессии и создаем новую
            PosifloraSession.objects.all().delete()

            session = PosifloraSession.objects.create(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

            self.stdout.write(self.style.SUCCESS('[OK] Сессия Posiflora успешно инициализирована!'))
            self.stdout.write(f'  Session ID: {session.id}')
            self.stdout.write(f'  Access Token: {access_token[:20]}...')
            self.stdout.write(f'  Expires At: {expires_at}')

        except requests.exceptions.HTTPError as e:
            raise CommandError(f'HTTP ошибка при подключении к API: {e}\nОтвет: {e.response.text}')
        except requests.exceptions.RequestException as e:
            raise CommandError(f'Ошибка при подключении к API: {e}')
        except Exception as e:
            raise CommandError(f'Неожиданная ошибка: {e}')
