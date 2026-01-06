from django.urls import path
from .views import CartView, CartItemView

urlpatterns = [
    path('', CartView.as_view()),
    path('item/', CartItemView.as_view()),
]