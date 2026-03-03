from rest_framework import serializers
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'name', 'size', 'price', 'image']
        read_only_fields = ['id']


class CartItemSerializer(serializers.Serializer):
    productId = serializers.CharField(max_length=50)
    size = serializers.ChoiceField(choices=['S', 'M', 'L'], required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    title = serializers.CharField(max_length=255)
    image = serializers.URLField(max_length=255)


class DeliverySerializer(serializers.Serializer):
    fullAddress = serializers.CharField()
    apartment = serializers.CharField(required=False, allow_blank=True)
    entrance = serializers.CharField(required=False, allow_blank=True)
    floor = serializers.CharField(required=False, allow_blank=True)
    intercom = serializers.CharField(required=False, allow_blank=True)
    date = serializers.CharField()
    time = serializers.CharField()
    district = serializers.CharField()


class PickupSerializer(serializers.Serializer):
    recipientName = serializers.CharField(max_length=255)
    recipientPhone = serializers.CharField(max_length=20)
    date = serializers.CharField()
    time = serializers.CharField()


class RecipientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    phoneNumber = serializers.CharField(max_length=20)


class OrderCreateSerializer(serializers.Serializer):
    cartItems = CartItemSerializer(many=True)
    deliveryType = serializers.ChoiceField(choices=['delivery', 'pickup'], default='delivery')
    delivery = DeliverySerializer(required=False)
    recipient = RecipientSerializer(required=False)
    pickup = PickupSerializer(required=False)
    sender = RecipientSerializer()
    postcard = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    deliveryPrice = serializers.DecimalField(max_digits=10, decimal_places=2)
    cartPrice = serializers.DecimalField(max_digits=10, decimal_places=2)
    fullPrice = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_cartItems(self, value):
        if not value:
            raise serializers.ValidationError("Zakazh dolzhen soderzhat' hotya by odin tovar")
        return value

    def validate(self, data):
        delivery_type = data.get('deliveryType', 'delivery')
        if delivery_type == 'delivery':
            if not data.get('delivery'):
                raise serializers.ValidationError({"delivery": "Informaciya o dostavke obyazatelna"})
            if not data.get('recipient'):
                raise serializers.ValidationError({"recipient": "Informaciya o poluchatele obyazatelna"})
        elif delivery_type == 'pickup':
            if not data.get('pickup'):
                raise serializers.ValidationError({"pickup": "Informaciya o samovyvoza obyazatelna"})
        return data


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_type_display = serializers.CharField(source='get_delivery_type_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user',
            'delivery_type', 'delivery_type_display',
            'sender_name', 'sender_phone',
            'full_address', 'apartment', 'entrance', 'floor', 'intercom',
            'date', 'time', 'district',
            'recipent_name', 'recipent_phone', 'postcart',
            'total_amount', 'delivery_cost', 'status', 'status_display',
            'payment_id', 'items',
            'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = ['id', 'user', 'total_amount', 'status', 'payment_id', 'created_at', 'updated_at', 'paid_at']


class PaymentResponseSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_id = serializers.CharField()
    payment_url = serializers.URLField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class PaymentStatusSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    status = serializers.CharField()
    paid = serializers.BooleanField()
    amount = serializers.CharField(allow_null=True)
    order_id = serializers.IntegerField()