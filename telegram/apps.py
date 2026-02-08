from django.apps import AppConfig


class TelegramConfig(AppConfig):
    name = 'apps.telegram'

    def ready(self):
        """
        Импортируем signals при запуске приложения
        """
        import signals
