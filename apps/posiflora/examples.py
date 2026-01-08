"""
Примеры использования Posiflora API в проекте
"""

# ============================================================
# ПРИМЕР 1: Простое получение товаров во view
# ============================================================

from rest_framework.views import APIView
from rest_framework.response import Response
from apps.posiflora.services.products import get_product_service


class ProductCatalogView(APIView):
    """
    Простой каталог товаров с пагинацией
    GET /api/catalog/?page=1
    """

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        try:
            service = get_product_service()
            result = service.get_products_page(
                page=page,
                page_size=page_size,
                public_only=True
            )

            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=500
            )


# ============================================================
# ПРИМЕР 2: Поиск товаров
# ============================================================

class ProductSearchView(APIView):
    """
    Поиск товаров
    GET /api/catalog/search/?q=роза
    """

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)

        page = int(request.query_params.get('page', 1))

        try:
            service = get_product_service()
            result = service.search_products(query=query, page=page)

            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


# ============================================================
# ПРИМЕР 3: Получение деталей товара
# ============================================================

class ProductDetailView(APIView):
    """
    Детали конкретного товара
    GET /api/catalog/{product_id}/
    """

    def get(self, request, product_id):
        try:
            service = get_product_service()
            product = service.get_product_by_id(product_id)

            return Response(product)
        except Exception as e:
            return Response(
                {'error': 'Product not found', 'detail': str(e)},
                status=404
            )


# ============================================================
# ПРИМЕР 4: Добавление товара Posiflora в корзину
# ============================================================

from apps.cart.models import CartItem


class AddPosifloraProductToCartView(APIView):
    """
    Добавление товара из Posiflora в корзину
    POST /api/cart/add-posiflora/
    Body: {"product_id": "12345"}
    """

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)

        # Проверяем, что товар существует в Posiflora
        try:
            service = get_product_service()
            product = service.get_product_by_id(product_id)

            if not product.get('available'):
                return Response({'error': 'Product is not available'}, status=400)

        except Exception as e:
            return Response({'error': 'Product not found in Posiflora'}, status=404)

        # Добавляем в корзину (CartItem хранит только product_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=request.user.cart,
            product_id=product_id
        )

        return Response({
            'message': 'Product added to cart',
            'product': product,
            'created': created
        })


# ============================================================
# ПРИМЕР 5: Получение товаров корзины с данными из Posiflora
# ============================================================

class CartWithProductDetailsView(APIView):
    """
    Получить корзину с полными данными о товарах из Posiflora
    GET /api/cart/details/
    """

    def get(self, request):
        cart = request.user.cart
        cart_items = cart.items.all()

        service = get_product_service()
        items_with_details = []

        for cart_item in cart_items:
            try:
                # Получаем данные товара из Posiflora
                product = service.get_product_by_id(cart_item.product_id)

                items_with_details.append({
                    'cart_item_id': cart_item.id,
                    'product': product
                })
            except Exception:
                # Если товар не найден в Posiflora, пропускаем
                continue

        return Response({
            'cart_id': cart.id,
            'items': items_with_details,
            'total_items': len(items_with_details)
        })


# ============================================================
# ПРИМЕР 6: Кэширование товаров
# ============================================================

from django.core.cache import cache


def get_cached_product(product_id, cache_time=300):
    """
    Получить товар с кэшированием на 5 минут

    Args:
        product_id: ID товара
        cache_time: Время кэширования в секундах

    Returns:
        Dict с данными товара
    """
    cache_key = f'posiflora_product_{product_id}'

    # Проверяем кэш
    product = cache.get(cache_key)
    if product is not None:
        return product

    # Получаем из API
    service = get_product_service()
    product = service.get_product_by_id(product_id)

    # Сохраняем в кэш
    cache.set(cache_key, product, cache_time)

    return product


def get_cached_products_page(page=1, page_size=50, cache_time=300):
    """
    Получить страницу товаров с кэшированием

    Args:
        page: Номер страницы
        page_size: Размер страницы
        cache_time: Время кэширования в секундах

    Returns:
        Dict с товарами и мета-информацией
    """
    cache_key = f'posiflora_products_page_{page}_{page_size}'

    # Проверяем кэш
    result = cache.get(cache_key)
    if result is not None:
        return result

    # Получаем из API
    service = get_product_service()
    result = service.get_products_page(page=page, page_size=page_size)

    # Сохраняем в кэш
    cache.set(cache_key, result, cache_time)

    return result


# Использование в view:
class CachedProductCatalogView(APIView):
    """Каталог с кэшированием"""

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        result = get_cached_products_page(page=page, cache_time=600)  # 10 минут
        return Response(result)


# ============================================================
# ПРИМЕР 7: Вызов management commands программно
# ============================================================

from django.core.management import call_command
from io import StringIO


def initialize_posiflora_session_programmatically():
    """
    Инициализировать сессию программно
    Можно вызвать, например, в админке по кнопке
    """
    try:
        call_command('init_posiflora_session')
        return True, "Session initialized successfully"
    except Exception as e:
        return False, str(e)


def check_session_status():
    """
    Проверить статус сессии программно
    """
    output = StringIO()
    try:
        call_command('check_posiflora_session', stdout=output)
        return output.getvalue()
    except Exception as e:
        return f"Error: {e}"


# Использование в view:
class AdminPosifloraControlView(APIView):
    """
    Админская панель для управления Posiflora
    POST /api/admin/posiflora/init-session/
    GET /api/admin/posiflora/check-session/
    """

    def post(self, request):
        """Инициализировать сессию"""
        success, message = initialize_posiflora_session_programmatically()
        return Response({
            'success': success,
            'message': message
        }, status=200 if success else 500)

    def get(self, request):
        """Проверить сессию"""
        status_text = check_session_status()
        return Response({'status': status_text})


# ============================================================
# ПРИМЕР 8: Celery задачи для фоновой работы
# ============================================================

# Если у вас настроен Celery:
"""
from celery import shared_task
from django.core.management import call_command
from apps.posiflora.models import PosifloraSession
from django.utils import timezone


@shared_task
def refresh_posiflora_token_if_needed():
    '''
    Celery задача для автоматического обновления токена
    Запускать каждый час через celery beat
    '''
    session = PosifloraSession.objects.first()

    if not session:
        # Инициализируем, если нет сессии
        call_command('init_posiflora_session')
        return 'Session initialized'

    # Если токен истекает через час или уже истек
    time_left = (session.expires_at - timezone.now()).total_seconds()
    if time_left < 3600:
        call_command('refresh_posiflora_session')
        return 'Token refreshed'

    return f'Token OK, {int(time_left/3600)} hours left'


@shared_task
def sync_popular_products_to_cache():
    '''
    Celery задача для предварительного кэширования популярных товаров
    Запускать раз в 10 минут
    '''
    from django.core.cache import cache

    service = get_product_service()

    # Кэшируем первые 3 страницы
    for page in range(1, 4):
        cache_key = f'posiflora_products_page_{page}_50'
        result = service.get_products_page(page=page, page_size=50)
        cache.set(cache_key, result, 600)  # 10 минут

    return 'Cached 3 pages of products'


# В settings.py добавить:
CELERY_BEAT_SCHEDULE = {
    'refresh-posiflora-token': {
        'task': 'apps.posiflora.tasks.refresh_posiflora_token_if_needed',
        'schedule': 3600.0,  # каждый час
    },
    'cache-popular-products': {
        'task': 'apps.posiflora.tasks.sync_popular_products_to_cache',
        'schedule': 600.0,  # каждые 10 минут
    },
}
"""


# ============================================================
# ПРИМЕР 9: Middleware для автоматической проверки сессии
# ============================================================

"""
from django.utils.deprecation import MiddlewareMixin
from apps.posiflora.models import PosifloraSession
from django.utils import timezone


class PosifloraSessionMiddleware(MiddlewareMixin):
    '''
    Middleware для автоматической проверки токена Posiflora
    при каждом запросе к API товаров
    '''

    def process_request(self, request):
        # Проверяем только для запросов к Posiflora API
        if not request.path.startswith('/api/posiflora/'):
            return None

        session = PosifloraSession.objects.first()
        if not session:
            # Можно редиректить на страницу ошибки
            return None

        # Проверяем, не истек ли токен
        if session.is_expired():
            from apps.posiflora.services.tokens import refresh_session
            try:
                refresh_session(session)
            except Exception:
                pass

        return None


# Добавить в settings.py:
MIDDLEWARE = [
    # ... другие middleware
    'apps.posiflora.middleware.PosifloraSessionMiddleware',
]
"""


# ============================================================
# ПРИМЕР 10: Использование в Django Admin
# ============================================================

"""
from django.contrib import admin
from apps.posiflora.models import PosifloraSession
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command


@admin.register(PosifloraSession)
class PosifloraSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'expires_at', 'is_expired_display', 'created_at', 'updated_at']
    readonly_fields = ['access_token_display', 'refresh_token_display', 'created_at', 'updated_at']

    def is_expired_display(self, obj):
        return '✗ Истек' if obj.is_expired() else '✓ Действителен'
    is_expired_display.short_description = 'Статус'

    def access_token_display(self, obj):
        return f'{obj.access_token[:50]}...'
    access_token_display.short_description = 'Access Token'

    def refresh_token_display(self, obj):
        return f'{obj.refresh_token[:50]}...'
    refresh_token_display.short_description = 'Refresh Token'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('init-session/', self.admin_site.admin_view(self.init_session_view), name='posiflora_init_session'),
            path('refresh-token/', self.admin_site.admin_view(self.refresh_token_view), name='posiflora_refresh_token'),
        ]
        return custom_urls + urls

    def init_session_view(self, request):
        '''Кнопка "Инициализировать сессию" в админке'''
        try:
            call_command('init_posiflora_session')
            messages.success(request, 'Сессия Posiflora успешно инициализирована!')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')

        return redirect('..')

    def refresh_token_view(self, request):
        '''Кнопка "Обновить токен" в админке'''
        try:
            call_command('refresh_posiflora_session')
            messages.success(request, 'Токен успешно обновлен!')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')

        return redirect('..')

    # Добавить кнопки в шаблон changelist
    change_list_template = 'admin/posiflora/posiflorasession/change_list.html'
"""


# ============================================================
# ПРИМЕР 11: Обработка ошибок и retry
# ============================================================

import time
from requests.exceptions import RequestException


def get_product_with_retry(product_id, max_retries=3, delay=1):
    """
    Получить товар с повторными попытками при ошибках

    Args:
        product_id: ID товара
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах

    Returns:
        Dict с данными товара

    Raises:
        Exception: Если все попытки неудачны
    """
    service = get_product_service()

    for attempt in range(max_retries):
        try:
            return service.get_product_by_id(product_id)
        except RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            raise e


# ============================================================
# ПРИМЕР 12: Фильтрация и сортировка товаров
# ============================================================

class FilteredProductsView(APIView):
    """
    Получить товары с фильтрацией и сортировкой на стороне бэкенда
    GET /api/catalog/filtered/?category=Розы&min_price=100&max_price=500
    """

    def get(self, request):
        # Получаем параметры фильтрации
        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        sort_by = request.query_params.get('sort_by', 'name')  # name, price

        try:
            # Получаем все товары (или первую страницу)
            service = get_product_service()
            result = service.get_products_page(page=1, page_size=100)
            products = result['products']

            # Фильтруем на стороне бэкенда
            if category:
                products = [p for p in products if p.get('category') == category]

            if min_price:
                products = [p for p in products if p.get('price', 0) >= float(min_price)]

            if max_price:
                products = [p for p in products if p.get('price', 0) <= float(max_price)]

            # Сортируем
            if sort_by == 'price':
                products = sorted(products, key=lambda x: x.get('price', 0))
            elif sort_by == 'name':
                products = sorted(products, key=lambda x: x.get('name', ''))

            return Response({
                'products': products,
                'count': len(products)
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)
