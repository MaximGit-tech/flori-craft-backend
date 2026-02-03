from rest_framework import serializers
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в заказе"""
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'name', 'size', 'price']
        read_only_fields = ['id']


class OrderItemCreateSerializer(serializers.Serializer):
    """Сериализатор для создания товара в заказе из корзины"""
    product_id = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=255)
    size = serializers.ChoiceField(choices=['L', 'M', 'S'])
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказа"""
    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'sender_name', 'sender_phone',
            'full_address', 'apartment', 'entrance', 'floor', 'intercom',
            'date', 'time', 'district',
            'recipent_name', 'recipent_phone', 'postcart',
            'delivery_cost', 'items'
        ]
        extra_kwargs = {
            'sender_name': {'required': True},
            'sender_phone': {'required': True},
            'full_address': {'required': True},
            'date': {'required': True},
            'time': {'required': True},
            'district': {'required': True},
        }

    def validate_items(self, value):
        """Проверка что есть хотя бы один товар"""
        if not value:
            raise serializers.ValidationError("Заказ должен содержать хотя бы один товар")
        return value


class OrderDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения заказа"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_display = serializers.CharField(source='get_time_display', read_only=True)
    district_display = serializers.CharField(source='get_district_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user',
            'sender_name', 'sender_phone',
            'full_address', 'apartment', 'entrance', 'floor', 'intercom',
            'date', 'time', 'time_display', 'district', 'district_display',
            'recipent_name', 'recipent_phone', 'postcart',
            'total_amount', 'delivery_cost', 'status', 'status_display',
            'payment_id', 'items',
            'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = ['id', 'user', 'total_amount', 'status', 'payment_id', 'created_at', 'updated_at', 'paid_at']


class PaymentResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа с информацией о платеже"""
    order_id = serializers.IntegerField()
    payment_id = serializers.CharField()
    payment_url = serializers.URLField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class PaymentStatusSerializer(serializers.Serializer):
    """Сериализатор для проверки статуса платежа"""
    payment_id = serializers.CharField()
    status = serializers.CharField()
    paid = serializers.BooleanField()
    amount = serializers.CharField(allow_null=True)
    order_id = serializers.IntegerField()
