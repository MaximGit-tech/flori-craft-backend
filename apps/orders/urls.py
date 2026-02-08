from django.urls import path
from apps.orders.views import (
    CreateOrderView,
    CheckPaymentView,
    YooKassaWebhookView,
    OrderDetailView,
    TelegramAdminRegisterView,
    TelegramAdminCheckView,
    TelegramOrdersListView
)

urlpatterns = [
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/check-payment/', CheckPaymentView.as_view(), name='check-payment'),
    path('webhook/', YooKassaWebhookView.as_view(), name='yookassa-webhook'),
    path('telegram/register/', TelegramAdminRegisterView.as_view(), name='telegram-admin-register'),
    path('telegram/check/<int:chat_id>/', TelegramAdminCheckView.as_view(), name='telegram-admin-check'),
    path('telegram/orders/<int:chat_id>/', TelegramOrdersListView.as_view(), name='telegram-orders-list'),
]