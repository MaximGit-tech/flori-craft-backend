import uuid
from decimal import Decimal
from typing import Optional, Dict, Any

from yookassa import Configuration, Payment
from yookassa.domain.common import ConfirmationType
from yookassa.domain.request import PaymentRequestBuilder

from django.conf import settings


class YooKassaService:
    """Сервис для работы с платежами через ЮКассу"""
    
    def __init__(self):
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
    
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

        if user_email:
            payment_data["receipt"] = {
                "customer": {
                    "email": user_email
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1",
                        "amount": {
                            "value": str(amount),
                            "currency": "RUB"
                        },
                        "vat_code": 1 
                    }
                ]
            }
        
        payment = Payment.create(payment_data, idempotence_key)
        
        return {
            'payment_id': payment.id,
            'payment_url': payment.confirmation.confirmation_url,
            'status': payment.status,
            'paid': payment.paid
        }
    
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
    def verify_webhook_signature(request_body: str, signature: str) -> bool:
        """
        Проверяет подпись webhook от ЮКассы

        Args:
            request_body: Тело запроса
            signature: Подпись из заголовка (не используется в ЮКassa)

        Returns:
            True если подпись валидна
        """
        # TODO: ЮKassa НЕ использует криптографические подписи для webhook.
        # Вместо этого они используют:
        #
        # 1. IP Whitelist - разрешить только запросы с IP адресов ЮКассы:
        #    - 185.71.76.0/27
        #    - 185.71.77.0/27
        #    - 77.75.153.0/25
        #    - 77.75.156.11
        #    - 77.75.156.35
        #    - 77.75.154.128/25
        #    - 2a02:5180::/32
        #
        # 2. HTTP Basic Auth - настроить в личном кабинете ЮКассы
        #    и проверять заголовок Authorization
        #
        # Реализация:
        # def verify_webhook(request):
        #     # Проверка IP
        #     client_ip = request.META.get('REMOTE_ADDR')
        #     allowed_ips = ['185.71.76.0/27', ...]  # см. выше
        #     if not ip_in_network(client_ip, allowed_ips):
        #         return False
        #
        #     # Или проверка HTTP Basic Auth
        #     auth_header = request.META.get('HTTP_AUTHORIZATION')
        #     if auth_header != f'Basic {expected_credentials}':
        #         return False
        #
        #     return True
        #
        # Документация: https://yookassa.ru/developers/using-api/webhooks#notification-security
        return True