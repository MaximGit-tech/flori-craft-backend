from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
import logging

from apps.orders.models import Order, OrderItem
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    PaymentResponseSerializer,
    PaymentStatusSerializer
)
from apps.orders.services import YooKassaService
from apps.cart.models import Cart
from drf_spectacular.utils import extend_schema, OpenApiResponse


logger = logging.getLogger(__name__)


class CreateOrderView(APIView):
    """Создание заказа с инициализацией платежа"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OrderCreateSerializer,
        responses={
            201: PaymentResponseSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            500: OpenApiResponse(description="Ошибка создания платежа")
        },
        tags=['Orders']
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                items_data = serializer.validated_data.pop('items')

                items_total = sum(Decimal(item['price']) for item in items_data)
                delivery_cost = serializer.validated_data.get('delivery_cost', Decimal('0'))
                total_amount = items_total + delivery_cost

                order = serializer.save(
                    user=request.user,
                    total_amount=total_amount
                )

                order_items = [
                    OrderItem(
                        order=order,
                        product_id=item['product_id'],
                        name=item['name'],
                        size=item['size'],
                        price=item['price']
                    )
                    for item in items_data
                ]
                OrderItem.objects.bulk_create(order_items)

                try:
                    cart = Cart.objects.get(user=request.user)
                    cart.items.all().delete()
                except Cart.DoesNotExist:
                    pass

                yookassa_service = YooKassaService()

                # URL для возврата после оплаты (нужно будет настроить на фронтенде)
                return_url = request.data.get('return_url', 'https://flori-craft-front.vercel.app/orders/success')

                payment_result = yookassa_service.create_payment(
                    amount=total_amount,
                    order_id=order.id,
                    description=f"Оплата заказа №{order.id}",
                    return_url=return_url,
                    user_email=getattr(request.user, 'email', None),
                    user_phone=serializer.validated_data.get('sender_phone')
                )

                order.payment_id = payment_result['payment_id']
                order.save(update_fields=['payment_id'])

                return Response({
                    'order_id': order.id,
                    'payment_id': payment_result['payment_id'],
                    'payment_url': payment_result['payment_url'],
                    'status': payment_result['status'],
                    'amount': str(total_amount)
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            return Response(
                {'error': 'Не удалось создать заказ и инициализировать платеж'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckPaymentView(APIView):
    """Проверка статуса платежа"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: PaymentStatusSerializer,
            404: OpenApiResponse(description="Заказ не найден"),
            500: OpenApiResponse(description="Ошибка проверки платежа")
        },
        tags=['Orders']
    )
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)

            if not order.payment_id:
                return Response(
                    {'error': 'У заказа нет связанного платежа'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            yookassa_service = YooKassaService()
            payment_info = yookassa_service.check_payment(order.payment_id)

            if payment_info['paid'] and order.status == 'pending':
                order.status = 'paid'
                order.paid_at = timezone.now()
                order.save(update_fields=['status', 'paid_at'])

            return Response({
                'payment_id': payment_info['payment_id'],
                'status': payment_info['status'],
                'paid': payment_info['paid'],
                'amount': payment_info['amount'],
                'order_id': order.id
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response(
                {'error': 'Заказ не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Ошибка при проверке платежа: {str(e)}")
            return Response(
                {'error': 'Не удалось проверить статус платежа'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class YooKassaWebhookView(APIView):
    """Обработка webhook уведомлений от ЮКассы"""
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        exclude=True
    )
    def post(self, request):
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR')

        yookassa_service = YooKassaService()
        if not yookassa_service.verify_webhook_ip(client_ip):
            logger.warning(f"Webhook от неавторизованного IP: {client_ip}")
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        try:
            data = json.loads(request.body)

            logger.info(f"Получен webhook от ЮКассы: {data}")

            event_type = data.get('event')
            if event_type != 'payment.succeeded':
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

            payment_object = data.get('object', {})
            payment_id = payment_object.get('id')
            payment_status = payment_object.get('status')
            metadata = payment_object.get('metadata', {})
            order_id = metadata.get('order_id')

            if not order_id:
                logger.error("В webhook отсутствует order_id")
                return Response({'error': 'Missing order_id'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                order = Order.objects.get(id=order_id, payment_id=payment_id)

                if payment_status == 'succeeded' and order.status == 'pending':
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                    order.save(update_fields=['status', 'paid_at'])
                    logger.info(f"Заказ {order_id} успешно оплачен")

                return Response({'status': 'ok'}, status=status.HTTP_200_OK)

            except Order.DoesNotExist:
                logger.error(f"Заказ {order_id} с payment_id {payment_id} не найден")
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        except json.JSONDecodeError:
            logger.error("Ошибка парсинга JSON в webhook")
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderListView(APIView):
    """Получение списка заказов пользователя"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OrderDetailSerializer(many=True)},
        tags=['Orders']
    )
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items')
        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """Получение деталей заказа"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OrderDetailSerializer,
            404: OpenApiResponse(description="Заказ не найден")
        },
        tags=['Orders']
    )
    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related('items').get(
                id=order_id,
                user=request.user
            )
            serializer = OrderDetailSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Заказ не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
