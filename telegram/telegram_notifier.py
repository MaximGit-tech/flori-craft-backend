import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramBotNotifier:
    """Отправка уведомлений в Telegram бот через FastAPI"""
    
    def __init__(self):
        self.bot_api_url = settings.TELEGRAM_BOT_API_URL
        self.api_key = settings.TELEGRAM_BOT_API_KEY
    
    def send_order_notification(self, order):
        """
        Отправляет заказ в Telegram бот
        
        Args:
            order: Объект модели Order
        """
        order_data = self._format_order(order)
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.post(
                f"{self.bot_api_url}/api/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Заказ #{order.id} отправлен в бот. "
                    f"Уведомлений: {result.get('notifications_sent', 0)}"
                )
                return True
            else:
                logger.error(
                    f"❌ Ошибка отправки заказа #{order.id}: "
                    f"{response.status_code} - {response.text}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка подключения к боту: {e}")
            return False
    
    def _format_order(self, order):
        """
        Конвертирует Django Order в формат для FastAPI бота
        """
        products = []
        for item in order.items.all():
            products.append({
                "name": item.name,
                "size": item.get_size_display() if item.size else None
            })

        delivery_time = None
        if order.time:
            time_dict = dict(order.DELIVERY_TIME_CHOICES)
            delivery_time = time_dict.get(order.time, order.time)

        district = None
        if order.district:
            district_dict = dict(order.DELIVERY_DISTRICT_CHOICES)
            district = district_dict.get(order.district, order.district)
        
        return {
            "order_number": f"FL-{order.id}",
            "recipient_name": order.recipent_name or "Не указано",
            "recipient_phone": order.recipent_phone or "Не указано",
            "address": order.full_address,
            "apartment": order.apartment,
            "entrance": order.entrance,
            "floor": order.floor,
            "intercom": order.intercom,
            "district": district,
            "delivery_date": order.date,
            "delivery_time": delivery_time,
            "products": products,
            "total_amount": float(order.total_amount)
        }