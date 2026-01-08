from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.posiflora.models import PosifloraSession


class Command(BaseCommand):
    help = 'Проверка статуса сессии Posiflora'

    def handle(self, *args, **options):
        try:
            session = PosifloraSession.objects.first()

            if not session:
                self.stdout.write(self.style.ERROR('✗ Сессия Posiflora не найдена'))
                self.stdout.write(self.style.WARNING(
                    'Выполните команду: python manage.py init_posiflora_session'
                ))
                return

            self.stdout.write(self.style.SUCCESS('✓ Сессия Posiflora найдена'))
            self.stdout.write(f'  Session ID: {session.id}')
            self.stdout.write(f'  Access Token: {session.access_token[:20]}...')
            self.stdout.write(f'  Refresh Token: {session.refresh_token[:20]}...')
            self.stdout.write(f'  Expires At: {session.expires_at}')
            self.stdout.write(f'  Created At: {session.created_at}')
            self.stdout.write(f'  Updated At: {session.updated_at}')

            # Проверяем, истек ли токен
            now = timezone.now()
            time_left = session.expires_at - now

            if session.is_expired():
                self.stdout.write(self.style.ERROR('\n✗ Токен истек!'))
                self.stdout.write(self.style.WARNING(
                    'Токен будет автоматически обновлен при следующем запросе к API'
                ))
            elif time_left.total_seconds() < 3600:  # меньше часа
                minutes_left = int(time_left.total_seconds() / 60)
                self.stdout.write(self.style.WARNING(
                    f'\n⚠ Токен скоро истечет! Осталось: {minutes_left} минут'
                ))
            else:
                hours_left = int(time_left.total_seconds() / 3600)
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Токен действителен. Осталось: {hours_left} часов'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
