from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.db_cart import get_items
from apps.cart.serializers import CartItemSerializer


class CartView(APIView):
    @extend_schema(
        summary="Получить корзину",
        description="Возвращает список всех товаров в корзине пользователя",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'items': {
                        'type': 'array',
                        'description': 'Список товаров в корзине',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 1},
                                'product_id': {'type': 'string', 'example': 'prod-123'},
                                'quantity': {'type': 'integer', 'example': 2},
                                'added_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'unauthorized'
                    }
                }
            }
        },
        tags=['Cart'],
        examples=[
            OpenApiExample(
                'Успешное получение корзины',
                value={
                    'items': [
                        {
                            'id': 1,
                            'product_id': 'prod-123',
                            'quantity': 2
                        }
                    ]
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: неавторизован',
                value={'error': 'unauthorized'},
                response_only=True,
                status_codes=['401']
            )
        ]
    )
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        items = get_items(request.user)
        serializer = CartItemSerializer(items, many=True)

        return Response({
            'items': serializer.data
        })


class CartItemView(APIView):
    @extend_schema(
        summary="Добавить товар в корзину",
        description="Добавляет товар в корзину пользователя по product_id",
        request={
            'type': 'object',
            'properties': {
                'product_id': {
                    'type': 'string',
                    'description': 'ID товара для добавления',
                    'example': 'prod-123'
                }
            },
            'required': ['product_id']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'example': 'ok'
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'product_id required'
                    }
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'unauthorized'
                    }
                }
            }
        },
        tags=['Cart'],
        examples=[
            OpenApiExample(
                'Успешное добавление',
                value={'status': 'ok'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствует product_id',
                value={'error': 'product_id required'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Запрос добавления товара',
                value={'product_id': 'prod-123'},
                request_only=True
            )
        ]
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id required'},
                status=400
            )

        from .services.db_cart import add_item
        add_item(request.user, product_id)

        return Response({'status': 'ok'})

    @extend_schema(
        summary="Удалить товар из корзины",
        description="Удаляет товар из корзины пользователя по product_id",
        request={
            'type': 'object',
            'properties': {
                'product_id': {
                    'type': 'string',
                    'description': 'ID товара для удаления',
                    'example': 'prod-123'
                }
            },
            'required': ['product_id']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'example': 'ok'
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'product_id required'
                    }
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'unauthorized'
                    }
                }
            }
        },
        tags=['Cart'],
        examples=[
            OpenApiExample(
                'Успешное удаление',
                value={'status': 'ok'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствует product_id',
                value={'error': 'product_id required'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Запрос удаления товара',
                value={'product_id': 'prod-123'},
                request_only=True
            )
        ]
    )
    def delete(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id required'},
                status=400
            )

        from .services.db_cart import remove_item
        remove_item(request.user, product_id)

        return Response({'status': 'ok'})