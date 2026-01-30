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
        # Пропускаем инициализацию для команд управления миграциями и тестов
        if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'test', 'check']):
            return

        # Импортируем здесь, чтобы избежать циклических импортов
        from .services.tokens import get_session

        try:
            # Проверяем учетные данные
            username = getattr(settings, 'POSIFLORA_USER', None)
            password = getattr(settings, 'POSIFLORA_PASSWORD', None)

            if not username or not password:
                logger.warning(
                    'Posiflora credentials not configured. '
                    'Set POSIFLORA_USER and POSIFLORA_PASSWORD in settings.'
                )
                return

            # get_session() автоматически создаст/обновит сессию при необходимости
            get_session()
            logger.info('Posiflora session is ready')

        except Exception as e:
            logger.error(f'Failed to initialize Posiflora session: {e}')
