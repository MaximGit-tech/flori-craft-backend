"""
Management команда для инициализации сессии Posiflora
"""
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.posiflora.models import PosifloraSession
from datetime import datetime


class Command(BaseCommand):
    help = 'Инициализация сессии Posiflora'

    def handle(self, *args, **options):
        self.stdout.write('Инициализация сессии Posiflora...')

        # Получаем учетные данные из настроек
        username = settings.POSIFLORA_USER
        password = settings.POSIFLORA_PASSWORD
        url = settings.POSIFLORA_URL

        if not username or not password:
            self.stdout.write(self.style.ERROR(
                'POSIFLORA_USER и POSIFLORA_PASSWORD должны быть установлены в .env'
            ))
            return

        try:
            # Создаем новую сессию через API
            self.stdout.write('Отправка запроса авторизации...')
            response = requests.post(
                f'{url}/sessions',
                headers={'Content-Type': 'application/vnd.api+json'},
                json={
                    'data': {
                        'type': 'sessions',
                        'attributes': {
                            'login': username,
                            'password': password
                        }
                    }
                }
            )
            response.raise_for_status()

            data = response.json()['data']['attributes']

            access_token = data['accessToken']
            refresh_token = data['refreshToken']
            expires_at_str = data.get('expireAt') or data.get('expireAT')

            # Парсим дату истечения
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))

            # Удаляем старые сессии
            PosifloraSession.objects.all().delete()

            # Создаем новую сессию
            session = PosifloraSession.objects.create(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )

            self.stdout.write(self.style.SUCCESS(
                f'Сессия успешно создана. Истекает: {expires_at}'
            ))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при запросе к API: {e}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка: {e}'
            ))
