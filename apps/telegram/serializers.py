"""
Serializers для Telegram моделей
Добавьте это в apps/orders/serializers.py
"""
from rest_framework import serializers
from apps.orders.models import TelegramAdmin


class TelegramAdminSerializer(serializers.ModelSerializer):
    """Сериализатор для модели TelegramAdmin"""
    
    class Meta:
        model = TelegramAdmin
        fields = [
            'id',
            'chat_id',
            'username',
            'first_name',
            'last_name',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']