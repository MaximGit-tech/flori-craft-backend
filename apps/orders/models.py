from django.db import models
from apps.custom_auth.models import CustomUser


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    DELIVERY_TIME_CHOICES = [
        ('1', '10:00-12:00'),
        ('2', '12:00-14:00'),
        ('3', '14:00-16:00'),
        ('4', '16:00-18:00'),
        ('5', '18:00-20:00'),
        ('6', '20:00-22:00'),
    ]

    DELIVERY_DISTRICT_CHOICES = [
        ('JK', 'FiliGrad, Only, Beregovoy'),
        ('FILI', 'Fili'),
        ('MKAD', 'MKAD'),
        ('NMKAD', 'Outside MKAD'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    sender_name = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=20)
    
    full_address = models.TextField()
    apartment = models.CharField(max_length=10, null=True, blank=True)
    entrance = models.CharField(max_length=10, null=True, blank=True)
    floor = models.CharField(max_length=10, null=True, blank=True)
    intercom = models.CharField(max_length=10, null=True, blank=True)

    date = models.CharField(max_length=10)
    time = models.CharField(choices=DELIVERY_TIME_CHOICES)
    district = models.CharField(choices=DELIVERY_DISTRICT_CHOICES)

    recipent_name = models.CharField(max_length=255, null=True, blank=True)
    recipent_phone = models.CharField(max_length=20, null=True, blank=True)

    postcart = models.TextField(null=True, blank=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    payment_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    SIZE_CHOICES = [
        ('L', 'Large'),
        ('M', 'Medium'),
        ('S', 'Small')
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_id = models.CharField(max_length=50)
    item_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(max_length=255)
