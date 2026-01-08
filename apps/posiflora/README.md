# Posiflora Integration

Интеграция с API Posiflora для получения товаров цветочного магазина.

## Содержание

1. [Установка и настройка](#установка-и-настройка)
2. [Management Commands](#management-commands)
3. [Использование в коде](#использование-в-коде)
4. [API Endpoints](#api-endpoints)
5. [Примеры использования](#примеры-использования)

---

## Установка и настройка

### 1. Добавьте переменные окружения в `.env`:

```env
POSIFLORA_URL=https://floricraft.posiflora.com/api/v1
POSIFLORA_USER=ваш_логин
POSIFLORA_PASSWORD=ваш_пароль
```

### 2. Выполните миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Инициализируйте сессию Posiflora:

```bash
python manage.py init_posiflora_session
```

---

## Management Commands

Management commands - это специальные команды Django, которые запускаются через `python manage.py`.

### 1. `init_posiflora_session` - Инициализация сессии

**Что делает:** Подключается к API Posiflora, получает токены доступа и сохраняет их в базу данных.

**Когда использовать:**
- При первом запуске проекта
- Когда нужно полностью пересоздать сессию
- После изменения учетных данных

**Примеры запуска:**

```bash
# Использовать данные из .env
python manage.py init_posiflora_session

# Указать данные явно
python manage.py init_posiflora_session --username "myuser" --password "mypass"

# Указать другой URL API
python manage.py init_posiflora_session --url "https://custom.posiflora.com/api/v1"
```

**Что происходит внутри:**
1. Отправляется POST запрос на `/sessions` с логином и паролем
2. Получаются `access_token`, `refresh_token`, `expires_at`
3. Старые сессии удаляются из БД
4. Новая сессия сохраняется в таблицу `PosifloraSession`

---

### 2. `check_posiflora_session` - Проверка сессии

**Что делает:** Показывает информацию о текущей сессии и проверяет, не истек ли токен.

**Когда использовать:**
- Для диагностики проблем с API
- Чтобы узнать, когда истекает токен
- В процессе разработки для проверки состояния

**Пример запуска:**

```bash
python manage.py check_posiflora_session
```

**Пример вывода:**

```
✓ Сессия Posiflora найдена
  Session ID: 1
  Access Token: eyJhbGciOiJIUzI1NiIs...
  Refresh Token: eyJhbGciOiJIUzI1NiIs...
  Expires At: 2026-01-09 15:30:00
  Created At: 2026-01-08 15:30:00
  Updated At: 2026-01-08 15:30:00

✓ Токен действителен. Осталось: 23 часов
```

---

### 3. `refresh_posiflora_session` - Обновление токена

**Что делает:** Вручную обновляет токен доступа используя refresh token.

**Когда использовать:**
- Для тестирования механизма обновления токенов
- Если токен истек и нужно его обновить вручную

**Примечание:** Токен обновляется автоматически при запросах к API, поэтому эта команда нужна редко.

**Пример запуска:**

```bash
python manage.py refresh_posiflora_session
```

---

### 4. `test_posiflora_api` - Тестирование API

**Что делает:** Пробует получить товары из API и выводит их на экран.

**Когда использовать:**
- Для проверки, что всё работает корректно
- После настройки интеграции
- Для диагностики проблем

**Пример запуска:**

```bash
# Показать 5 товаров (по умолчанию)
python manage.py test_posiflora_api

# Показать 10 товаров
python manage.py test_posiflora_api --limit 10
```

**Пример вывода:**

```
Подключение к Posiflora API...
Получение товаров...

✓ Успешно получено товаров: 5

Мета-информация:
  Всего товаров: 1247
  Текущая страница: 1
  Размер страницы: 5

Первые 5 товаров:

1. Роза красная 50см
   ID: 12345
   Цена: 150.0 RUB
   Доступен: Да
   Категория: Розы

2. Тюльпан желтый
   ID: 12346
   Цена: 80.0 RUB
   Доступен: Да
   Категория: Тюльпаны
...
```

---

## Использование в коде

### Вариант 1: Использование сервиса (рекомендуется)

Создан специальный сервис `PosifloraProductService` для работы с API.

```python
# В любом месте вашего кода (views, tasks, etc.)
from apps.posiflora.services.products import get_product_service

# Получить экземпляр сервиса
service = get_product_service()

# Получить все товары
all_products = service.get_all_products(public_only=True)

# Получить одну страницу товаров
result = service.get_products_page(page=1, page_size=50)
products = result['products']
meta = result['meta']

# Получить конкретный товар
product = service.get_product_by_id('12345')

# Поиск товаров
search_result = service.search_products(query='роза', page=1)
```

### Вариант 2: Вызов management command программно

Вы можете вызывать management commands из Python кода:

```python
from django.core.management import call_command
from io import StringIO

# Инициализировать сессию программно
call_command('init_posiflora_session',
             username='myuser',
             password='mypass')

# Проверить сессию и получить вывод
output = StringIO()
call_command('check_posiflora_session', stdout=output)
result = output.getvalue()

# Тестировать API
call_command('test_posiflora_api', limit=10)
```

**Когда это полезно:**
- В Celery задачах для периодической проверки сессии
- В админке для кнопок "Обновить токены"
- В тестах для настройки окружения

### Вариант 3: Прямая работа с моделью сессии

```python
from apps.posiflora.models import PosifloraSession
from apps.posiflora.services.tokens import get_session, refresh_session

# Получить текущую сессию
session = get_session()  # Автоматически обновит токен если истек

# Проверить, истек ли токен
if session.is_expired():
    session = refresh_session(session)

# Получить токен для запросов
access_token = session.access_token
```

---

## API Endpoints

После настройки доступны следующие endpoints:

### 1. Список товаров с пагинацией

```http
GET /api/posiflora/products/?page=1&page_size=50&public_only=true
```

**Query параметры:**
- `page` - номер страницы (default: 1)
- `page_size` - размер страницы (default: 50)
- `public_only` - только публичные товары (default: true)
- `on_window` - товары на витрине (optional: true/false)

**Ответ:**
```json
{
  "products": [
    {
      "id": "12345",
      "name": "Роза красная 50см",
      "description": "Красивая красная роза",
      "sku": "ROSE-RED-50",
      "price": "150.00",
      "currency": "RUB",
      "available": true,
      "image_url": "https://...",
      "category": "Розы"
    }
  ],
  "meta": {
    "page": {
      "number": 1,
      "size": 50,
      "total": 1247
    }
  }
}
```

### 2. Все товары (без пагинации)

```http
GET /api/posiflora/products/all/?public_only=true
```

**Внимание:** Может быть медленным при большом количестве товаров!

### 3. Конкретный товар

```http
GET /api/posiflora/products/{product_id}/
```

### 4. Поиск товаров

```http
GET /api/posiflora/products/search/?q=роза&page=1&page_size=50
```

---

## Примеры использования

### Пример 1: Отображение товаров на frontend

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.posiflora.services.products import get_product_service

class CatalogView(APIView):
    def get(self, request):
        page = int(request.query_params.get('page', 1))

        service = get_product_service()
        result = service.get_products_page(page=page, page_size=20)

        return Response(result)
```

### Пример 2: Добавление товара в корзину

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.posiflora.services.products import get_product_service
from apps.cart.models import CartItem

class AddToCartView(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')

        # Проверяем, что товар существует в Posiflora
        service = get_product_service()
        try:
            product = service.get_product_by_id(product_id)
        except:
            return Response({'error': 'Product not found'}, status=404)

        # Добавляем в корзину (сохраняем только ID)
        cart_item, created = CartItem.objects.get_or_create(
            cart=request.user.cart,
            product_id=product_id
        )

        return Response({
            'message': 'Added to cart',
            'product': product
        })
```

### Пример 3: Celery задача для проверки токенов

```python
# tasks.py
from celery import shared_task
from django.core.management import call_command
from apps.posiflora.models import PosifloraSession
from django.utils import timezone

@shared_task
def check_posiflora_session():
    """Проверка и обновление токена Posiflora если нужно"""
    session = PosifloraSession.objects.first()

    if not session:
        # Инициализируем сессию
        call_command('init_posiflora_session')
        return 'Session initialized'

    # Проверяем истечение через час
    time_left = session.expires_at - timezone.now()
    if time_left.total_seconds() < 3600:  # меньше часа
        call_command('refresh_posiflora_session')
        return 'Session refreshed'

    return 'Session OK'


# Запускать каждый час
# settings.py
CELERY_BEAT_SCHEDULE = {
    'check-posiflora-session': {
        'task': 'apps.posiflora.tasks.check_posiflora_session',
        'schedule': 3600.0,  # каждый час
    },
}
```

### Пример 4: Кэширование товаров

```python
# services/cached_products.py
from django.core.cache import cache
from apps.posiflora.services.products import get_product_service

def get_cached_products(cache_time=300):  # 5 минут
    """Получить товары с кэшированием"""
    cache_key = 'posiflora_products_all'

    # Проверяем кэш
    products = cache.get(cache_key)
    if products is not None:
        return products

    # Получаем из API
    service = get_product_service()
    products = service.get_all_products()

    # Сохраняем в кэш
    cache.set(cache_key, products, cache_time)

    return products
```

---

## Автоматизация

### Cron задача для обновления токенов (на сервере)

Добавьте в crontab:

```bash
# Проверка токена каждый час
0 * * * * cd /path/to/project && python manage.py refresh_posiflora_session
```

### Supervisor для периодических задач

```ini
# /etc/supervisor/conf.d/posiflora-refresh.conf
[program:posiflora-refresh]
command=/path/to/venv/bin/python /path/to/project/manage.py refresh_posiflora_session
directory=/path/to/project
autostart=false
autorestart=false
stdout_logfile=/var/log/posiflora-refresh.log
```

---

## Troubleshooting

### Ошибка: "Posiflora session not initialized"

**Решение:**
```bash
python manage.py init_posiflora_session
```

### Ошибка: "HTTP 401 Unauthorized"

**Причины:**
1. Токен истек (должен обновиться автоматически)
2. Неверные учетные данные

**Решение:**
```bash
# Проверить сессию
python manage.py check_posiflora_session

# Переинициализировать
python manage.py init_posiflora_session
```

### Ошибка: "Connection timeout"

**Причины:**
1. Проблемы с сетью
2. Неверный POSIFLORA_URL

**Решение:**
Проверьте переменную `POSIFLORA_URL` в `.env`

---

## Дополнительная информация

- Токены автоматически обновляются при запросах к API
- Сессия хранится в таблице `posiflora_posiflorasession`
- Товары НЕ сохраняются в базу данных (прокси-режим)
- Все запросы к API проходят через сервис `PosifloraProductService`
