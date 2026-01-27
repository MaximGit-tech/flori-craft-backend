from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .services.products import get_product_service
from .serializers import (
    ProductSerializer,
    BouquetSerializer,
    CategorizedProductsSerializer,
)


class ProductDetailView(APIView):
    """
    API endpoint для получения конкретного товара по ID
    """

    @extend_schema(
        summary="Получить товар по ID",
        description="Возвращает детальную информацию о товаре из Posiflora API по его ID",
        responses={
            200: ProductSerializer,
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'}
                }
            }
        },
        tags=['Bouquets'],
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': '12345',
                    'name': 'Роза красная 50см',
                    'description': 'Красивая красная роза',
                    'sku': 'ROSE-RED-50',
                    'price': '150.00',
                    'currency': 'RUB',
                    'available': True,
                    'image_url': 'https://example.com/image.jpg',
                    'category': 'Розы',
                    'item_type': 'flower',
                    'price_min': '150.00',
                    'price_max': '150.00'
                },
                response_only=True,
            ),
        ]
    )
    def get(self, request, product_id):
        try:
            service = get_product_service()
            product = service.get_product_by_id(product_id)

            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Product not found', 'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


class BouquetListView(APIView):
    """
    API endpoint для получения всех букетов
    """

    @extend_schema(
        summary="Получить все букеты",
        description="Возвращает список всех букетов из Posiflora Shop API",
        responses={
            200: {
                'type': 'array',
                'items': {'$ref': '#/components/schemas/Bouquet'}
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'}
                }
            }
        },
        tags=['Bouquets'],
        examples=[
            OpenApiExample(
                'Success Response',
                value=[
                    {
                        'id': '5b53929f-4c56-498e-8b5c-cb369ad6c7bb',
                        'title': 'Букет с Амариллисами и Нерине',
                        'description': 'Красивый букет',
                        'image_urls': [
                            'https://cdn.posiflora.online/6866/images/z/c100ab6f89d894c05fd34ceb9a0899a3c7c2b312.jpg',
                            'https://cdn.posiflora.online/6866/images/z/c100ab6f89d894c05fd34ceb9a0899a3c7c2b312_medium.jpg',
                            'https://cdn.posiflora.online/6866/images/z/c100ab6f89d894c05fd34ceb9a0899a3c7c2b312_shop.jpg'
                        ],
                        'price': 10200
                    }
                ],
                response_only=True,
            ),
        ]
    )
    def get(self, request):
        try:
            service = get_product_service()
            bouquets = service.fetch_bouquets()

            serializer = BouquetSerializer(bouquets, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Failed to fetch bouquets', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class ProductsInStock(APIView):
    """
    API endpoint для получения товаров из базы посифлоры с вариантами
    """

    @extend_schema(
        summary="Получить товары с вариантами",
        description="Возвращает спецификации из Posiflora API с вариантами размеров, сгруппированные по категориям",
        responses={
            200: CategorizedProductsSerializer,
            500: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'}
                }
            }
        },
        tags=['Bouquets'],
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'categories': [
                        {
                            'name': 'Авторские букеты',
                            'products': [
                                {
                                    'title': 'Букет Максим',
                                    'description': '',
                                    'image_urls': [
                                        'https://cdn.posiflora.online/6866/images/z/image1.jpg',
                                        'https://cdn.posiflora.online/6866/images/z/image2.jpg'
                                    ],
                                    'variants': [
                                        {'size': 'S', 'price': 4050},
                                        {'size': 'M', 'price': 3150}
                                    ]
                                },
                                {
                                    'title': 'Ваза',
                                    'description': '',
                                    'image_urls': [
                                        'https://cdn.posiflora.online/6866/images/z/vase.jpg'
                                    ],
                                    'price': 0
                                }
                            ]
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    )
    def get(self, request):
        try:
            service = get_product_service()
            specifications_data = service.fetch_specifications()

            serializer = CategorizedProductsSerializer(specifications_data)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Failed to fetch specifications', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
