from django.core.management.base import BaseCommand, CommandError
from apps.posiflora.models import PosifloraSession
from apps.posiflora.services.tokens import refresh_session


class Command(BaseCommand):
    help = 'Обновить токен доступа Posiflora (refresh token)'

    def handle(self, *args, **options):
        try:
            session = PosifloraSession.objects.first()

            if not session:
                raise CommandError(
                    'Сессия Posiflora не найдена. '
                    'Выполните команду: python manage.py init_posiflora_session'
                )

            self.stdout.write('Обновление токена...')
            self.stdout.write(f'Текущий токен истекает: {session.expires_at}')

            # Обновляем сессию
            updated_session = refresh_session(session)

            self.stdout.write(self.style.SUCCESS('\n✓ Токен успешно обновлен!'))
            self.stdout.write(f'  Новый токен истекает: {updated_session.expires_at}')
            self.stdout.write(f'  Access Token: {updated_session.access_token[:20]}...')

        except Exception as e:
            raise CommandError(f'Ошибка при обновлении токена: {e}')
