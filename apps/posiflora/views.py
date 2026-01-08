from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.products import get_product_service
from .serializers import ProductSerializer


class ProductListView(APIView):
    """
    GET /api/posiflora/products/

    Получить ВСЕ товары (без пагинации)

    Query параметры:
    - public_only: только публичные товары (по умолчанию true)
    - on_window: товары на витрине (true/false, опционально)
    """

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
    GET /api/posiflora/products/{id}/

    Получить конкретный товар по ID
    """

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
