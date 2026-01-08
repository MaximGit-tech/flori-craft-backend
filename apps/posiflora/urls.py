from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
)

app_name = 'posiflora'

urlpatterns = [
    # Все товары
    path('products/', ProductListView.as_view(), name='product-list'),

    # Конкретный товар
    path('products/<str:product_id>/', ProductDetailView.as_view(), name='product-detail'),
]
