from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    BouquetListView,
    ProductsByCategoryView,
    SpecificationsView,
)

app_name = 'posiflora'

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name='product-detail'),

    path('bouquets/', BouquetListView.as_view(), name='bouquet-list'),
    path('products-by-category/', ProductsByCategoryView.as_view(), name='products-by-category'),
    path('specifications/', SpecificationsView.as_view(), name='specifications'),
]
