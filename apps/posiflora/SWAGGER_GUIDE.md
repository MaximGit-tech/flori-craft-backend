# Swagger/OpenAPI Документация

Swagger документация автоматически генерируется для всех API endpoints проекта FloriCraft.

## Доступ к документации

После запуска сервера документация доступна по следующим URL:

### 1. Swagger UI (интерактивная документация)
```
http://localhost:8000/api/docs/
```
Swagger UI - это интерактивный интерфейс, который позволяет:
- Просматривать все доступные endpoints
- Тестировать API прямо в браузере
- Видеть примеры запросов и ответов
- Авторизоваться и делать запросы с токенами

### 2. ReDoc (альтернативная документация)
```
http://localhost:8000/api/redoc/
```
ReDoc - это красивый интерфейс документации с лучшей читаемостью для больших API.

### 3. OpenAPI Schema (JSON)
```
http://localhost:8000/api/schema/
```
Сырая OpenAPI схема в формате JSON для использования в других инструментах.

---

## Как использовать Swagger UI

### Шаг 1: Откройте Swagger UI

Перейдите на `http://localhost:8000/api/docs/`

### Шаг 2: Просмотр endpoints

Все endpoints сгруппированы по тегам:
- **Posiflora Products** - работа с товарами из Posiflora
- **Cart** - управление корзиной
- **Auth** - аутентификация

### Шаг 3: Тестирование endpoint

1. Кликните на endpoint, который хотите протестировать
2. Нажмите кнопку **"Try it out"**
3. Заполните параметры (если требуются)
4. Нажмите **"Execute"**
5. Посмотрите ответ сервера

### Шаг 4: Авторизация (если требуется)

Если endpoint требует авторизации:
1. Нажмите кнопку **"Authorize"** вверху страницы
2. Введите токен или credentials
3. Нажмите **"Authorize"**
4. Теперь можно делать авторизованные запросы

---

## Примеры использования

### Получить все товары

**Endpoint:** `GET /api/posiflora/products/`

**В Swagger UI:**
1. Откройте секцию "Posiflora Products"
2. Кликните на `GET /api/posiflora/products/`
3. Нажмите "Try it out"
4. (Опционально) Измените параметры:
   - `public_only`: true/false
   - `on_window`: true/false
5. Нажмите "Execute"

**Пример ответа:**
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
      "image_url": "https://example.com/image.jpg",
      "category": "Розы",
      "item_type": "flower",
      "price_min": "150.00",
      "price_max": "150.00"
    }
  ],
  "count": 1247
}
```

### Получить товар по ID

**Endpoint:** `GET /api/posiflora/products/{product_id}/`

**В Swagger UI:**
1. Откройте секцию "Posiflora Products"
2. Кликните на `GET /api/posiflora/products/{product_id}/`
3. Нажмите "Try it out"
4. Введите `product_id` (например: "12345")
5. Нажмите "Execute"

---

## Интеграция с другими инструментами

### Postman

1. Скачайте OpenAPI схему: `http://localhost:8000/api/schema/`
2. В Postman: File → Import → Raw text
3. Вставьте содержимое схемы
4. Готово! Все endpoints импортированы в Postman

### Insomnia

1. Скачайте OpenAPI схему: `http://localhost:8000/api/schema/`
2. В Insomnia: Create → Import from File
3. Выберите скачанный файл схемы
4. Готово!

### curl

Из Swagger UI можно скопировать готовую команду curl:
1. После выполнения запроса в Swagger UI
2. Найдите секцию "Curl"
3. Скопируйте команду

Пример:
```bash
curl -X 'GET' \
  'http://localhost:8000/api/posiflora/products/?public_only=true' \
  -H 'accept: application/json'
```

---

## Настройка документации

Документация настраивается в файле `settings.py`:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'FloriCraft API',
    'DESCRIPTION': 'API для цветочного интернет-магазина FloriCraft',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
}
```

### Добавление документации к новым endpoints

При создании нового view используйте декоратор `@extend_schema`:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class MyView(APIView):
    @extend_schema(
        summary="Краткое описание",
        description="Подробное описание endpoint",
        parameters=[
            OpenApiParameter(
                name='my_param',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Описание параметра',
                required=False,
            ),
        ],
        responses={
            200: MySerializer,
            400: {'description': 'Bad Request'}
        },
        tags=['My Tag'],
    )
    def get(self, request):
        pass
```

---

## Troubleshooting

### Документация не открывается

**Проблема:** 404 ошибка при открытии `/api/docs/`

**Решение:**
1. Проверьте, что `drf-spectacular` установлен: `pip list | grep drf-spectacular`
2. Проверьте `INSTALLED_APPS` в settings.py - должен быть `'drf_spectacular'`
3. Проверьте `REST_FRAMEWORK` в settings.py - должен быть `'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'`

### Endpoints не отображаются

**Проблема:** В документации отсутствуют некоторые endpoints

**Решение:**
1. Убедитесь, что views наследуются от DRF классов (APIView, ViewSet, etc.)
2. Добавьте декоратор `@extend_schema` к методам view
3. Проверьте, что URLs правильно подключены в главном urls.py

### Ошибка при генерации схемы

**Проблема:** Ошибка при открытии `/api/schema/`

**Решение:**
1. Проверьте serializers - они должны быть валидными
2. Убедитесь, что все import'ы корректны
3. Запустите: `python manage.py spectacular --file schema.yml --validate`

---

## Полезные ссылки

- [drf-spectacular документация](https://drf-spectacular.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redocly.com/redoc/)

---

## Примеры для разработки

### Минимальный пример документации

```python
from drf_spectacular.utils import extend_schema

class ProductView(APIView):
    @extend_schema(
        summary="Получить товары",
        tags=['Products'],
    )
    def get(self, request):
        return Response({"products": []})
```

### Полный пример с параметрами и примерами

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

class ProductView(APIView):
    @extend_schema(
        summary="Получить товары",
        description="Возвращает список всех товаров с фильтрацией",
        parameters=[
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Фильтр по категории',
                required=False,
                examples=[
                    OpenApiExample('Розы', value='roses'),
                    OpenApiExample('Тюльпаны', value='tulips'),
                ]
            ),
        ],
        responses={
            200: ProductSerializer(many=True),
            400: {'description': 'Invalid parameters'}
        },
        tags=['Products'],
        examples=[
            OpenApiExample(
                'Успешный ответ',
                value={'products': [{'id': '1', 'name': 'Роза'}]},
                response_only=True,
            ),
        ]
    )
    def get(self, request):
        return Response({"products": []})
```

---

Теперь ваш API полностью задокументирован и готов к использованию! 🎉
