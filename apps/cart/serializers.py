from rest_framework import serializers
from apps.cart.models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ('product_id', 'title', 'size', 'price', 'image')


class CartItemInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=64)
    title = serializers.CharField(max_length=255)
    size = serializers.ChoiceField(choices=['S', 'M', 'L'], required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    image = serializers.CharField(max_length=500)