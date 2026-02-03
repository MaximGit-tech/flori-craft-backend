from django.urls import path
from apps.orders.views import (
    CreateOrderView,
    CheckPaymentView,
    YooKassaWebhookView,
    OrderListView,
    OrderDetailView
)

urlpatterns = [
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('list/', OrderListView.as_view(), name='order-list'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/check-payment/', CheckPaymentView.as_view(), name='check-payment'),
    path('webhook/', YooKassaWebhookView.as_view(), name='yookassa-webhook'),
]
