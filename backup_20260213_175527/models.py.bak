from django.db import models
from django.utils import timezone


class PosifloraSession(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at