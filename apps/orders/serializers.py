from rest_framework import serializers
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в заказе"""
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'name', 'size', 'price', 'image']
        read_only_fields = ['id']


class CartItemSerializer(serializers.Serializer):
    """Сериализатор для элемента корзины"""
    productId = serializers.CharField(max_length=50)
    size = serializers.ChoiceField(choices=['S', 'M', 'L'], required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    title = serializers.CharField(max_length=255)
    image = serializers.URLField(max_length=255)


class DeliverySerializer(serializers.Serializer):
    """Сериализатор для информации о доставке"""
    fullAddress = serializers.CharField()
    apartment = serializers.CharField(required=False, allow_blank=True)
    entrance = serializers.CharField(required=False, allow_blank=True)
    floor = serializers.CharField(required=False, allow_blank=True)
    intercom = serializers.CharField()
    date = serializers.CharField()
    time = serializers.CharField()
    district = serializers.CharField()


class RecipientSerializer(serializers.Serializer):
    """Сериализатор для информации о получателе/отправителе"""
    name = serializers.CharField(max_length=255)
    phoneNumber = serializers.CharField(max_length=20)


class OrderCreateSerializer(serializers.Serializer):
    """Сериализатор для создания заказа"""
    cartItems = CartItemSerializer(many=True)
    delivery = DeliverySerializer()
    recipient = RecipientSerializer()
    sender = RecipientSerializer()
    postcard = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    deliveryPrice = serializers.DecimalField(max_digits=10, decimal_places=2)
    cartPrice = serializers.DecimalField(max_digits=10, decimal_places=2)
    fullPrice = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_cartItems(self, value):
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
