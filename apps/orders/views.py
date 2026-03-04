from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from django.core.signing import Signer, BadSignature
from decimal import Decimal
import json
import logging

from apps.orders.models import Order, OrderItem, TelegramAdmin
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    PaymentResponseSerializer,
    PaymentStatusSerializer
)
from apps.orders.services import YooKassaService
from apps.orders.telegram_service import TelegramNotificationService
from apps.cart.models import Cart
from apps.custom_auth.models import CustomUser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.custom_auth.services.sms_code import send_sms


logger = logging.getLogger(__name__)


def unsign_user_id(signed_user_id):
    if not signed_user_id:
        return None
    try:
        signer = Signer(salt='user-auth')
        return signer.unsign(signed_user_id)
    except BadSignature:
        return None


class CreateOrderView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=OrderCreateSerializer,
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='ID polzovatelya (podpisannyy)',
                required=True
            )
        ],
        responses={
            201: PaymentResponseSerializer,
            400: OpenApiResponse(description="Oshibka validacii"),
            404: OpenApiResponse(description="Polzovatel ne nayden"),
            500: OpenApiResponse(description="Oshibka sozdaniya platezha")
        },
        tags=['Orders']
    )
    def post(self, request):
        signed_user_id = request.GET.get('user_id')
        user_id = unsign_user_id(signed_user_id)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            user = None

        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                validated_data = serializer.validated_data

                cart_items = validated_data['cartItems']
                delivery_type = validated_data.get('deliveryType', 'delivery')
                sender = validated_data['sender']
                postcard = validated_data.get('postcard', '')
                delivery_price = validated_data['deliveryPrice']
                full_price = validated_data['fullPrice']

                # --- Создание заказа в зависимости от типа ---
                if delivery_type == 'pickup':
                    pickup = validated_data['pickup']
                    order = Order.objects.create(
                        user=user,
                        delivery_type='pickup',
                        sender_name=sender['name'],
                        sender_phone=sender['phoneNumber'],
                        # Адрес не нужен при самовывозе
                        full_address=None,
                        district=None,
                        date=pickup['date'],
                        time=pickup['time'],
                        # Получатель берётся из pickup
                        recipent_name=pickup['recipientName'],
                        recipent_phone=pickup['recipientPhone'],
                        postcart=postcard,
                        total_amount=full_price,
                        delivery_cost=Decimal('0'),
                    )
                else:
                    delivery = validated_data['delivery']
                    recipient = validated_data['recipient']
                    order = Order.objects.create(
                        user=user,
                        delivery_type='delivery',
                        sender_name=sender.get('name', ''),
                        sender_phone=sender.get('phoneNumber', ''),
                        full_address=delivery['fullAddress'],
                        apartment=delivery.get('apartment', ''),
                        entrance=delivery.get('entrance', ''),
                        floor=delivery.get('floor', ''),
                        intercom=delivery.get('intercom', ''),
                        date=delivery['date'],
                        time=delivery['time'],
                        district=delivery['district'],
                        recipent_name=recipient['name'],
                        recipent_phone=recipient['phoneNumber'],
                        postcart=postcard,
                        total_amount=full_price,
                        delivery_cost=delivery_price,
                    )

                order_items = [
                    OrderItem(
                        order=order,
                        product_id=item['productId'],
                        name=item['title'],
                        size=item.get('size', ''),
                        price=item['price'],
                        image=item['image']
                    )
                    for item in cart_items
                ]
                OrderItem.objects.bulk_create(order_items)

                try:
                    cart = Cart.objects.get(user=user)
                    cart.items.all().delete()
                except (Cart.DoesNotExist, TypeError):
                    pass

                yookassa_service = YooKassaService()
                return_url = request.data.get('return_url', 'https://floricraft.ru/thank-you')

                payment_result = yookassa_service.create_payment(
                    amount=full_price,
                    order_id=order.id,
                    description=f"Oplata zakaza #{order.id}",
                    return_url=return_url,
                    user_email=getattr(user, 'email', None),
                    user_phone=sender['phoneNumber']
                )

                order.payment_id = payment_result['payment_id']
                order.save(update_fields=['payment_id'])

                return Response({
                    'order_id': order.id,
                    'payment_id': payment_result['payment_id'],
                    'payment_url': payment_result['payment_url'],
                    'status': payment_result['status'],
                    'amount': str(full_price)
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Oshibka pri sozdanii zakaza: {type(e).__name__}: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Ne udalos sozdat zakaz', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckPaymentView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='ID polzovatelya (podpisannyy)',
                required=True
            )
        ],
        responses={
            200: PaymentStatusSerializer,
            400: OpenApiResponse(description="Nevernyy user_id"),
            404: OpenApiResponse(description="Zakaz ne nayden"),
            500: OpenApiResponse(description="Oshibka proverki platezha")
        },
        tags=['Orders']
    )
    def get(self, request, order_id):
        signed_user_id = request.GET.get('user_id')
        user_id = unsign_user_id(signed_user_id)

        if not user_id:
            return Response({'error': 'user_id required or invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            order = Order.objects.get(id=order_id, user=user)

            if not order.payment_id:
                return Response({'error': 'U zakaza net svyazannogo platezha'}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'error': 'Zakaz ne nayden'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Oshibka pri proverke platezha: {str(e)}")
            return Response({'error': 'Ne udalos proverit status platezha'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class YooKassaWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(exclude=True)
    def post(self, request):
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR')

        yookassa_service = YooKassaService()
        if not yookassa_service.verify_webhook_ip(client_ip):
            logger.warning(f"Webhook ot neavtorizovannogo IP: {client_ip}")
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        try:
            data = json.loads(request.body)
            logger.info(f"Polchen webhook ot YuKassy: {data}")

            event_type = data.get('event')
            if event_type != 'payment.succeeded':
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

            payment_object = data.get('object', {})
            payment_id = payment_object.get('id')
            payment_status = payment_object.get('status')
            metadata = payment_object.get('metadata', {})
            order_id = metadata.get('order_id')

            if not order_id:
                logger.error("V webhook otsutstvuet order_id")
                return Response({'error': 'Missing order_id'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                order = Order.objects.get(id=order_id, payment_id=payment_id)

                if payment_status == 'succeeded' and order.status == 'pending':
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                    order.save(update_fields=['status', 'paid_at'])
                    logger.info(f"Zakaz {order_id} uspeshno oplachen")

                    # --- Уведомление в Telegram ---
                    try:
                        telegram_service = TelegramNotificationService()
                        telegram_service.send_new_order_notification(order)
                    except Exception as e:
                        logger.error(f"Oshibka otpravki Telegram-uvedomleniya dlya zakaza {order.id}: {str(e)}")

                    # --- SMS-уведомление пользователю ---
                    try:
                        if order.delivery_type == 'pickup':
                            sms_message = (
                                f"FloriCraft: Заказ #{order.id} оплачен! "
                                f"Самовывоз {order.date} в {order.time}. "
                                f"Сумма: {order.total_amount} руб."
                            )
                        else:
                            time_display = dict(Order.DELIVERY_TIME_CHOICES).get(str(order.time), order.time)
                            sms_message = (
                                f"FloriCraft: Заказ #{order.id} оплачен! "
                                f"Доставка {order.date} {time_display}. "
                                f"Сумма: {order.total_amount} руб."
                            )

                        success, response_message = send_sms(order.sender_phone, sms_message)
                        if success:
                            logger.info(f"SMS uspeshno otpravleno na {order.sender_phone} dlya zakaza {order.id}")
                        else:
                            logger.error(f"Oshibka otpravki SMS dlya zakaza {order.id}: {response_message}")

                    except Exception as e:
                        logger.error(f"Isklyuchenie pri otpravke SMS dlya zakaza {order.id}: {str(e)}")

                return Response({'status': 'ok'}, status=status.HTTP_200_OK)

            except Order.DoesNotExist:
                logger.error(f"Zakaz {order_id} s payment_id {payment_id} ne nayden")
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        except json.JSONDecodeError:
            logger.error("Oshibka parsinga JSON v webhook")
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Oshibka obrabotki webhook: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='ID polzovatelya (podpisannyy)',
                required=True
            )
        ],
        responses={
            200: OrderDetailSerializer,
            400: OpenApiResponse(description="Nevernyy user_id"),
            404: OpenApiResponse(description="Zakaz ne nayden")
        },
        tags=['Orders']
    )
    def get(self, request, order_id):
        signed_user_id = request.GET.get('user_id')
        user_id = unsign_user_id(signed_user_id)

        if not user_id:
            return Response({'error': 'user_id required or invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            order = Order.objects.prefetch_related('items').get(id=order_id, user=user)
            serializer = OrderDetailSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Zakaz ne nayden'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramAdminRegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(exclude=True)
    def post(self, request):
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            if not chat_id:
                return Response({'error': 'chat_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            admin, created = TelegramAdmin.objects.update_or_create(
                chat_id=chat_id,
                defaults={
                    'username': data.get('username'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name'),
                    'is_active': True
                }
            )

            action = 'registered' if created else 'updated'
            return Response({'status': 'ok', 'action': action, 'chat_id': chat_id}, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TelegramAdminCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def get(self, request, chat_id):
        try:
            admin = TelegramAdmin.objects.get(chat_id=chat_id)
            return Response({
                'is_registered': True,
                'is_active': admin.is_active,
                'username': admin.username,
                'first_name': admin.first_name,
                'last_name': admin.last_name
            }, status=status.HTTP_200_OK)
        except TelegramAdmin.DoesNotExist:
            return Response({'is_registered': False, 'is_active': False}, status=status.HTTP_200_OK)


class TelegramOrdersListView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def get(self, request, chat_id):
        try:
            admin = TelegramAdmin.objects.get(chat_id=chat_id, is_active=True)
        except TelegramAdmin.DoesNotExist:
            return Response({'error': 'Administrator ne nayden ili neaktiven'}, status=status.HTTP_404_NOT_FOUND)

        orders = Order.objects.filter(status='paid').prefetch_related('items').order_by('-created_at')[:10]

        orders_data = []
        for order in orders:
            items_data = [
                {
                    'name': item.name,
                    'size': item.get_size_display() if item.size else None,
                    'price': str(item.price)
                }
                for item in order.items.all()
            ]

            time_display = dict(Order.DELIVERY_TIME_CHOICES).get(order.time, order.time)
            district_display = dict(Order.DELIVERY_DISTRICT_CHOICES).get(order.district, order.district) if order.district else None

            orders_data.append({
                'id': order.id,
                'delivery_type': order.delivery_type,
                'sender_name': order.sender_name,
                'sender_phone': order.sender_phone,
                'recipent_name': order.recipent_name,
                'recipent_phone': order.recipent_phone,
                'full_address': order.full_address,
                'date': order.date,
                'time': time_display,
                'district': district_display,
                'total_amount': str(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'paid_at': order.paid_at.isoformat() if order.paid_at else None,
                'items': items_data
            })

        return Response({'orders': orders_data, 'count': len(orders_data)}, status=status.HTTP_200_OK)