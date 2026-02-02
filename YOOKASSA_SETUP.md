# Настройка ЮKassa

## 1. Получение credentials

1. Зарегистрируйтесь на https://yookassa.ru/
2. Создайте магазин в личном кабинете
3. Перейдите в **Настройки → Данные для API**
4. Скопируйте:
   - `shopId` → `YOOKASSA_SHOP_ID`
   - `Секретный ключ` → `YOOKASSA_SECRET_KEY`

## 2. Добавление в .env

```bash
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=live_xxx...
```

## 3. Настройка webhook (важно!)

### Вариант 1: IP Whitelist (рекомендуется)

В вашем веб-сервере (nginx/railway) настройте whitelist для IP адресов ЮKassa:

```
185.71.76.0/27
185.71.77.0/27
77.75.153.0/25
77.75.156.11
77.75.156.35
77.75.154.128/25
2a02:5180::/32
```

### Вариант 2: HTTP Basic Auth

1. В личном кабинете ЮKassa: **Настройки → HTTP-уведомления**
2. Укажите URL: `https://your-domain.com/api/orders/webhook/`
3. Выберите события: `payment.succeeded`, `payment.canceled`
4. Установите логин и пароль для Basic Auth

В коде добавьте проверку:
```python
def webhook_view(request):
    # Проверка Basic Auth
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    # Validate auth header
    ...
```

## 4. Реализация webhook endpoint

TODO: Создать view для обработки webhook в `apps/orders/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from .services import YooKassaService

class YooKassaWebhookView(APIView):
    authentication_classes = []  # Webhook не требует авторизации пользователя
    permission_classes = []

    def post(self, request):
        # Проверка IP или Basic Auth
        # Обработка payment.succeeded, payment.canceled
        # Обновление статуса Order
        pass
```

## 5. Тестирование

В личном кабинете ЮKassa есть тестовый режим:
- Тестовый shopId и secret key
- Виртуальные платежи без списания денег
- Webhook можно тестировать через ngrok

## Документация

- API: https://yookassa.ru/developers/api
- Webhook: https://yookassa.ru/developers/using-api/webhooks
- SDK Python: https://github.com/yoomoney/yookassa-sdk-python
