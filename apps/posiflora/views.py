from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .services.products import get_product_service
from .serializers import ProductSerializer


class ProductListView(APIView):
    """
    API endpoint для получения всех товаров из Posiflora
    """

    @extend_schema(
        summary="Получить все товары",
        description="Возвращает полный список товаров из Posiflora API без пагинации",
        parameters=[
            OpenApiParameter(
                name='public_only',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Только публичные товары',
                required=False,
                default=True,
            ),
            OpenApiParameter(
                name='on_window',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Товары на витрине',
                required=False,
            ),
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'products': {
                        'type': 'array',
                        'items': {'$ref': '#/components/schemas/Product'}
                    },
                    'count': {
                        'type': 'integer',
                        'description': 'Общее количество товаров'
                    }
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'}
                }
            }
        },
        tags=['Posiflora Products'],
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'products': [
                        {
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
                        }
                    ],
                    'count': 1247
                },
                response_only=True,
            ),
        ]
    )
    def get(self, request):
        try:
            # Получаем параметры из запроса
            public_only = request.query_params.get('public_only', 'true').lower() == 'true'

            on_window = request.query_params.get('on_window')
            if on_window is not None:
                on_window = on_window.lower() == 'true'

            # Получаем все товары из API
            service = get_product_service()
            products = service.get_all_products(
                public_only=public_only,
                on_window=on_window,
            )

            # Сериализуем данные
            serializer = ProductSerializer(products, many=True)

            return Response({
                'products': serializer.data,
                'count': len(products)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Failed to fetch products', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        tags=['Posiflora Products'],
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
