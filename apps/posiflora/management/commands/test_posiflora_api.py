from django.core.management.base import BaseCommand, CommandError
from apps.posiflora.services.products import get_product_service


class Command(BaseCommand):
    help = 'Тестирование подключения к Posiflora API (получение товаров)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Количество товаров для вывода (по умолчанию 5)',
        )

    def handle(self, *args, **options):
        limit = options['limit']

        try:
            self.stdout.write('Подключение к Posiflora API...')

            # Получаем сервис
            service = get_product_service()

            # Получаем все товары
            self.stdout.write('Получение всех товаров...\n')
            products = service.get_all_products(public_only=True)

            if not products:
                self.stdout.write(self.style.WARNING('Товары не найдены'))
                return

            # Выводим информацию о товарах
            total_count = len(products)
            self.stdout.write(self.style.SUCCESS(f'✓ Успешно получено товаров: {total_count}'))

            # Показываем первые N товаров
            products_to_show = products[:limit]
            self.stdout.write(f'\nПервые {len(products_to_show)} товаров:\n')

            for i, product in enumerate(products_to_show, 1):
                self.stdout.write(self.style.SUCCESS(f'{i}. {product.get("name")}'))
                self.stdout.write(f'   ID: {product.get("id")}')
                self.stdout.write(f'   Цена: {product.get("price")} {product.get("currency")}')
                self.stdout.write(f'   Доступен: {"Да" if product.get("available") else "Нет"}')
                if product.get('category'):
                    self.stdout.write(f'   Категория: {product.get("category")}')
                if product.get('image_url'):
                    self.stdout.write(f'   Изображение: {product.get("image_url")}')
                self.stdout.write('')  # Пустая строка для разделения

            self.stdout.write(self.style.SUCCESS(f'\n✓ Тест успешно пройден! Всего товаров: {total_count}'))

        except Exception as e:
            raise CommandError(f'Ошибка при тестировании API: {e}')
