from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.signing import Signer, BadSignature
from .services.db_cart import get_items, add_item, remove_item
from apps.cart.serializers import CartItemSerializer, CartItemInputSerializer
from apps.custom_auth.models import CustomUser


def unsign_user_id(signed_user_id):
    """Расшифровывает подписанный user_id из cookie."""
    if not signed_user_id:
        return None
    try:
        signer = Signer(salt='user-auth')
        return signer.unsign(signed_user_id)
    except BadSignature:
        return None


class CartView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Получить корзину",
        description="Возвращает список всех товаров в корзине пользователя",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='ID пользователя (опционально, для совместимости). Должен совпадать с ID аутентифицированного пользователя.',
                required=False
            )
        ],
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
            },
            403: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Access denied'
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
            ),
            OpenApiExample(
                'Ошибка: доступ запрещен',
                value={'error': 'Access denied'},
                response_only=True,
                status_codes=['403']
            )
        ]
    )
    def get(self, request):
        signed_user_id = request.GET.get('user_id')
        user_id = unsign_user_id(signed_user_id)

        if not user_id:
            return Response({'error': 'user_id required or invalid signature'}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        items = get_items(user)
        serializer = CartItemSerializer(items, many=True)

        return Response({
            'items': serializer.data
        })


class CartItemView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Добавить товар в корзину",
        description="Добавляет товар в корзину пользователя",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='ID пользователя',
                required=True
            )
        ],
        request=CartItemInputSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'ok'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Access denied'}
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'User not found'}
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
                'Запрос добавления товара',
                value={
                    'product_id': 'prod-123',
                    'title': 'Букет роз',
                    'size': 'M',
                    'price': 2500.00,
                    'image': 'https://example.com/image.jpg'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        signed_user_id = request.GET.get('user_id')
        user_id = unsign_user_id(signed_user_id)
        if not user_id:
            return Response({'error': 'user_id required or invalid signature'}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        serializer = CartItemInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)

        add_item(user, serializer.validated_data)
        return Response({'status': 'ok'})

    @extend_schema(
        summary="Удалить товар из корзины",
        description="Удаляет товар из корзины пользователя по product_id и size",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='ID пользователя',
                required=True
            )
        ],
        request={
            'type': 'object',
            'properties': {
                'product_id': {'type': 'string', 'example': 'prod-123'},
                'size': {'type': 'string', 'enum': ['S', 'M', 'L'], 'example': 'M'}
            },
            'required': ['product_id']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'ok'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Access denied'}
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'User not found'}
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
                'Запрос удаления товара',
                value={'product_id': 'prod-123', 'size': 'M'},
                request_only=True
            )
        ]
    )
    def delete(self, request):
        signed_user_id = request.GET.get('user_id')
        user_id = unsign_user_id(signed_user_id)
        if not user_id:
            return Response({'error': 'user_id required or invalid signature'}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id required'}, status=400)

        item_data = {
            'product_id': product_id,
            'size': request.data.get('size'),
        }
        remove_item(user, item_data)
        return Response({'status': 'ok'})