from rest_framework import serializers
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в заказе"""
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'name', 'size', 'price']
        read_only_fields = ['id']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказа"""

    class Meta:
        model = Order
        fields = [
            'sender_name', 'sender_phone',
            'full_address', 'apartment', 'entrance', 'floor', 'intercom',
            'date', 'time', 'district',
            'recipient_name', 'recipient_phone', 'postcard',
            'delivery_cost'
        ]
        extra_kwargs = {
            'sender_name': {'required': True, 'allow_blank': False},
            'sender_phone': {'required': True, 'allow_blank': False},
            'address': {'required': True, 'allow_blank': False},
            'delivery_date': {'required': True},
            'delivery_time': {'required': True},
            'delivery_district': {'required': True},
        }