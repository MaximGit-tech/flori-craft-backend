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

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    
    address = models.TextField()
    apartment_number = models.CharField(max_length=10, null=True, blank=True)
    entrance_number = models.CharField(max_length=10, null=True, blank=True)
    floor = models.CharField(max_length=10, null=True, blank=True)
    intercom = models.CharField(max_length=10, null=True, blank=True)

