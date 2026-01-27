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


class BouquetSerializer(serializers.Serializer):
    """Serializer для букетов"""

    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=500)
    description = serializers.CharField(allow_blank=True, allow_null=True)
    image_urls = serializers.ListField(
        child=serializers.URLField(max_length=1000),
        allow_empty=True
    )
    price = serializers.IntegerField()


class ProductVariantSerializer(serializers.Serializer):
    """Serializer для вариантов продукта (размеры)"""

    size = serializers.ChoiceField(choices=['S', 'M', 'L'])
    price = serializers.IntegerField()


class CategoryProductSerializer(serializers.Serializer):
    """Serializer для продукта внутри категории"""

    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=500)
    description = serializers.CharField(allow_blank=True, allow_null=True)
    image_urls = serializers.ListField(
        child=serializers.URLField(max_length=1000),
        allow_empty=True
    )
    variants = ProductVariantSerializer(many=True, required=False)
    price = serializers.IntegerField(required=False, allow_null=True)


class CategorySerializer(serializers.Serializer):
    """Serializer для категории с продуктами"""

    name = serializers.CharField(max_length=500)
    products = CategoryProductSerializer(many=True)


class CategorizedProductsSerializer(serializers.Serializer):
    """Serializer для всех продуктов, сгруппированных по категориям"""

    categories = CategorySerializer(many=True)
