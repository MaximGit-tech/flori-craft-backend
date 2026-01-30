from django.db import models
from apps.custom_auth.models import CustomUser


class Cart(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    SIZE_CHOICES = [
        ('L', 'Large'),
        ('M', 'Medium'),
        ('S', 'Small')
    ]

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=1, choices=SIZE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('cart', 'product_id', 'size')