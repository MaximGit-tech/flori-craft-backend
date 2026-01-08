from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    """Serializer для товаров из Posiflora API"""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=500)
    description = serializers.CharField(allow_blank=True, allow_null=True)
    sku = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    currency = serializers.CharField(max_length=10, default='RUB')
    available = serializers.BooleanField(default=True)
    image_url = serializers.URLField(max_length=1000, allow_blank=True, allow_null=True)
    category = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    item_type = serializers.CharField(max_length=100, allow_blank=True, allow_null=True)
    price_min = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, required=False)
    price_max = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, required=False)
