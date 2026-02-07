import uuid
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from ipaddress import ip_address, ip_network

from yookassa import Configuration, Payment
from yookassa.domain.common import ConfirmationType
from yookassa.domain.request import PaymentRequestBuilder

from django.conf import settings


logger = logging.getLogger(__name__)


class YooKassaService:
    """Сервис для работы с платежами через ЮКассу"""

    def __init__(self):
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        # Определяем тестовый режим по типу секретного ключа
        self.is_test_mode = settings.YOOKASSA_SECRET_KEY.startswith('test_') if settings.YOOKASSA_SECRET_KEY else False
        logger.info(f"YooKassa инициализирована. Тестовый режим: {self.is_test_mode}")

    def create_payment(
        self,
        amount: Decimal,
        order_id: int,
        description: str,
        return_url: str,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает платеж в ЮКассе

        Args:
            amount: Сумма платежа
            order_id: ID заказа
            description: Описание платежа
            return_url: URL для возврата после оплаты
            user_email: Email пользователя (опционально)
            user_phone: Телефон пользователя (опционально)

        Returns:
            Dict с информацией о платеже
        """
        try:
            idempotence_key = str(uuid.uuid4())

            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": ConfirmationType.REDIRECT,
                    "return_url": return_url
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "order_id": order_id
                }
            }

            # Добавляем чек - обязателен если включена фискализация
            # Нужен хотя бы email или phone
            if user_email or user_phone:
                customer_data = {}
                if user_email:
                    customer_data["email"] = user_email
                if user_phone:
                    customer_data["phone"] = user_phone

                payment_data["receipt"] = {
                    "customer": customer_data,
                    "items": [
                        {
                            "description": description,
                            "quantity": "1.00",
                            "amount": {
                                "value": str(amount),
                                "currency": "RUB"
                            },
                            "vat_code": 1,
                            "payment_mode": "full_payment",
                            "payment_subject": "commodity"
                        }
                    ]
                }
                logger.info(f"Чек добавлен к платежу (email: {user_email}, phone: {user_phone})")
            else:
                logger.warning("Невозможно создать чек: не указан ни email, ни phone")

            logger.info(f"Создание платежа. Order ID: {order_id}, Amount: {amount}, Email: {user_email}")
            logger.debug(f"Payment data: {payment_data}")

            payment = Payment.create(payment_data, idempotence_key)

            logger.info(f"Платеж создан успешно. Payment ID: {payment.id}, Status: {payment.status}")

            return {
                'payment_id': payment.id,
                'payment_url': payment.confirmation.confirmation_url,
                'status': payment.status,
                'paid': payment.paid
            }
        except Exception as e:
            logger.error(f"Ошибка создания платежа в ЮКассе: {type(e).__name__}: {str(e)}")
            logger.error(f"Order ID: {order_id}, Amount: {amount}")
            raise

    def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверяет статус платежа

        Args:
            payment_id: ID платежа в ЮКассе

        Returns:
            Dict с информацией о платеже
        """
        payment = Payment.find_one(payment_id)

        return {
            'payment_id': payment.id,
            'status': payment.status,
            'paid': payment.paid,
            'amount': payment.amount.value if payment.amount else None,
            'created_at': payment.created_at.isoformat() if payment.created_at else None,
            'metadata': payment.metadata
        }

    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Отменяет платеж

        Args:
            payment_id: ID платежа в ЮКассе

        Returns:
            Dict с информацией о платеже
        """
        idempotence_key = str(uuid.uuid4())
        payment = Payment.cancel(payment_id, idempotence_key)

        return {
            'payment_id': payment.id,
            'status': payment.status,
            'cancelled': payment.status == 'canceled'
        }

    @staticmethod
    def verify_webhook_ip(client_ip: str) -> bool:
        """
        Проверяет IP-адрес webhook от ЮКассы

        Args:
            client_ip: IP адрес клиента

        Returns:
            True если IP адрес из белого списка ЮКассы
        """
        YOOKASSA_IPS = [
            '185.71.76.0/27',
            '185.71.77.0/27',
            '77.75.153.0/25',
            '77.75.156.11/32',
            '77.75.156.35/32',
            '77.75.154.128/25',
            '2a02:5180::/32',
        ]

        try:
            client = ip_address(client_ip)
            for allowed_network in YOOKASSA_IPS:
                if client in ip_network(allowed_network):
                    return True
            return False
        except ValueError:
            return False
