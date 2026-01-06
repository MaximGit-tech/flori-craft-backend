from datetime import timedelta
from django.db import models
from django.utils import timezone


class SmsCode(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=3)


class CustomUser(models.Model):
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone