# Posiflora Integration - Quick Start (без пагинации)

## Быстрый старт

### 1. Настройка переменных окружения

Добавьте в `.env` файл:

```env
POSIFLORA_URL=https://floricraft.posiflora.com/api/v1
POSIFLORA_USER=ваш_логин
POSIFLORA_PASSWORD=ваш_пароль
```

### 2. Выполните миграции

```bash
# Активируйте виртуальное окружение
.venv\Scripts\activate  # Windows
# или
source .venv/bin/activate  # Linux/Mac

# Выполните миграции
python manage.py makemigrations
python manage.py migrate
```

### 3. Инициализируйте сессию Posiflora

```bash
python manage.py init_posiflora_session
```

### 4. Проверьте работу

```bash
# Проверить статус сессии
python manage.py check_posiflora_session

# Протестировать API (получить первые 5 товаров)
python manage.py test_posiflora_api --limit 5
```

---

## API Endpoints (без пагинации)

### 1. Получить ВСЕ товары

```http
GET /api/posiflora/products/
```

**Query параметры:**
- `public_only` - только публичные товары (default: `true`)
- `on_window` - товары на витрине (optional: `true`/`false`)

**Пример:**
```bash
# Все публичные товары
curl http://localhost:8000/api/posiflora/products/

# Все товары (включая непубличные)
curl http://localhost:8000/api/posiflora/products/?public_only=false

# Только товары на витрине
curl http://localhost:8000/api/posiflora/products/?on_window=true
```

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
      "category": "Розы",
      "item_type": "flower",
      "price_min": "150.00",
      "price_max": "150.00"
    },
    ...
  ],
  "count": 1247
}
```

### 2. Получить конкретный товар

```http
GET /api/posiflora/products/{product_id}/
```

**Пример:**
```bash
curl http://localhost:8000/api/posiflora/products/12345/
```

**Ответ:**
```json
{
  "id": "12345",
  "name": "Роза красная 50см",
  "description": "Красивая красная роза",
  "sku": "ROSE-RED-50",
  "price": "150.00",
  "currency": "RUB",
  "available": true,
  "image_url": "https://...",
  "category": "Розы",
  "item_type": "flower",
  "price_min": "150.00",
  "price_max": "150.00"
}
```

### 3. Поиск товаров

```http
GET /api/posiflora/products/search/?q=роза
```

**Query параметры:**
- `q` - поисковый запрос (обязательно)

**Пример:**
```bash
curl http://localhost:8000/api/posiflora/products/search/?q=роза
```

**Ответ:**
```json
{
  "products": [
    {
      "id": "12345",
      "name": "Роза красная 50см",
      ...
    },
    {
      "id": "12346",
      "name": "Роза белая 60см",
      ...
    }
  ],
  "count": 42
}
```

---

## Использование в коде

### Простой пример

```python
from apps.posiflora.services.products import get_product_service

# В любом view или функции
def my_view(request):
    service = get_product_service()

    # Получить все товары
    all_products = service.get_all_products()

    # Получить конкретный товар
    product = service.get_product_by_id('12345')

    # Поиск товаров
    search_results = service.search_products('роза')

    return Response({
        'total': len(all_products),
        'product': product,
        'search_count': len(search_results)
    })
```

### Пример view для получения всех товаров

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.posiflora.services.products import get_product_service

class CatalogView(APIView):
    def get(self, request):
        try:
            service = get_product_service()
            products = service.get_all_products(public_only=True)

            return Response({
                'products': products,
                'count': len(products)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
```

### Пример добавления товара в корзину

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.posiflora.services.products import get_product_service
from apps.cart.models import CartItem

class AddToCartView(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')

        # Проверяем, что товар существует
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

---

## Management Commands

### `init_posiflora_session`
Инициализировать сессию Posiflora (получить токены)

```bash
# Использовать данные из .env
python manage.py init_posiflora_session

# Указать данные явно
python manage.py init_posiflora_session --username "myuser" --password "mypass"
```

### `check_posiflora_session`
Проверить статус сессии

```bash
python manage.py check_posiflora_session
```

### `refresh_posiflora_session`
Обновить токен доступа

```bash
python manage.py refresh_posiflora_session
```

### `test_posiflora_api`
Протестировать подключение к API

```bash
# Показать первые 5 товаров
python manage.py test_posiflora_api --limit 5

# Показать первые 20 товаров
python manage.py test_posiflora_api --limit 20
```

---

## Структура сервиса

### Методы `PosifloraProductService`:

```python
class PosifloraProductService:

    def get_all_products(
        public_only: bool = True,
        on_window: Optional[bool] = None
    ) -> List[Dict]:
        """Получить ВСЕ товары (проходит по всем страницам внутри)"""

    def get_product_by_id(product_id: str) -> Dict:
        """Получить конкретный товар по ID"""

    def search_products(query: str) -> List[Dict]:
        """Поиск товаров (возвращает все результаты)"""
```

---

## Важные замечания

1. **Пагинация убрана** - все методы возвращают полный список товаров
2. **Товары НЕ сохраняются в БД** - данные получаются напрямую из Posiflora API при каждом запросе
3. **Токены обновляются автоматически** - если токен истек, он обновится при следующем запросе
4. **Только session хранится в БД** - таблица `PosifloraSession` содержит только токены доступа

---

## Troubleshooting

### Ошибка: "Posiflora session not initialized"

**Решение:**
```bash
python manage.py init_posiflora_session
```

### Ошибка: "HTTP 401 Unauthorized"

**Решение:**
```bash
# Проверить сессию
python manage.py check_posiflora_session

# Переинициализировать
python manage.py init_posiflora_session
```

### Медленная загрузка товаров

**Причина:** API возвращает много товаров, требуется время на обработку всех страниц

**Решение:** Рассмотрите добавление кэширования:
```python
from django.core.cache import cache

def get_cached_products(cache_time=600):  # 10 минут
    cache_key = 'all_posiflora_products'

    products = cache.get(cache_key)
    if products is not None:
        return products

    service = get_product_service()
    products = service.get_all_products()

    cache.set(cache_key, products, cache_time)
    return products
```

---

## Готово!

Теперь вы можете:

1. Получать все товары через `/api/posiflora/products/`
2. Искать товары через `/api/posiflora/products/search/?q=запрос`
3. Получать конкретный товар через `/api/posiflora/products/{id}/`
4. Использовать сервис в коде: `get_product_service().get_all_products()`
