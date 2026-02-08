"""
URL маршруты для Telegram интеграции
Добавьте это в apps/orders/urls.py
"""
from django.urls import path
from apps.orders.views import (
    telegram_register_admin,
    telegram_check_admin,
    telegram_deactivate_admin,
    telegram_list_admins
)

urlpatterns = [
    path('telegram/register/', telegram_register_admin, name='telegram-register'),
    path('telegram/check/<int:chat_id>/', telegram_check_admin, name='telegram-check'),
    path('telegram/deactivate/<int:chat_id>/', telegram_deactivate_admin, name='telegram-deactivate'),
    path('telegram/admins/', telegram_list_admins, name='telegram-admins'),
]