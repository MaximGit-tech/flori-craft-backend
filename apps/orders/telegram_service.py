import requests
import logging
from django.conf import settings
from apps.orders.models import Order, TelegramAdmin

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Сервис для отправки уведомлений в Telegram бот"""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_new_order_notification(self, order: Order) -> bool:
        """
        Отправляет уведомление о новом оплаченном заказе всем активным администраторам

        Args:
            order: Объект заказа Order

        Returns:
            bool: True если уведомление отправлено хотя бы одному администратору, False в противном случае
        """
        if not self.bot_token:
            logger.warning("Telegram бот не настроен (отсутствует токен)")
            return False

        try:
            # Получаем всех активных администраторов
            admins = TelegramAdmin.objects.filter(is_active=True)

            if not admins.exists():
                logger.warning("Нет активных администраторов для отправки уведомлений")
                return False

            # Формируем текст уведомления
            message = self._format_order_message(order)

            # Отправляем сообщение каждому администратору
            success_count = 0
            url = f"{self.base_url}/sendMessage"

            for admin in admins:
                try:
                    payload = {
                        "chat_id": admin.chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }

                    response = requests.post(url, json=payload, timeout=10)

                    if response.status_code == 200:
                        success_count += 1
                        logger.info(f"Уведомление о заказе #{order.id} отправлено администратору {admin.chat_id}")
                    else:
                        logger.error(f"Ошибка отправки администратору {admin.chat_id}: {response.status_code}, {response.text}")

                except Exception as e:
                    logger.error(f"Ошибка при отправке администратору {admin.chat_id}: {str(e)}")

            if success_count > 0:
                logger.info(f"Уведомление о заказе #{order.id} отправлено {success_count}/{admins.count()} администраторам")
                return True
            else:
                logger.error(f"Не удалось отправить уведомление ни одному администратору")
                return False

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений в Telegram: {str(e)}")
            return False

    def _format_order_message(self, order: Order) -> str:
        """
        Форматирует сообщение о заказе

        Args:
            order: Объект заказа Order

        Returns:
            str: Отформатированное сообщение
        """
        time_display = dict(Order.DELIVERY_TIME_CHOICES).get(order.time, order.time)

        district_display = dict(Order.DELIVERY_DISTRICT_CHOICES).get(order.district, order.district)

        items_text = ""
        for item in order.items.all():
            size_display = f" ({item.get_size_display()})" if item.size else ""
            items_text += f"  • {item.name}{size_display} - {item.price} ₽\n"

        full_address = order.full_address
        address_details = []
        if order.apartment:
            address_details.append(f"кв. {order.apartment}")
        if order.entrance:
            address_details.append(f"подъезд {order.entrance}")
        if order.floor:
            address_details.append(f"этаж {order.floor}")
        if order.intercom:
            address_details.append(f"домофон {order.intercom}")

        if address_details:
            full_address += f" ({', '.join(address_details)})"

        message = f"""
<b>🎉 НОВЫЙ ЗАКАЗ #{order.id}</b>

<b>📦 Информация о заказе:</b>
💰 Сумма: {order.total_amount} ₽
🚚 Доставка: {order.delivery_cost} ₽
💳 ID платежа: {order.payment_id}

<b>👤 Отправитель:</b>
• Имя: {order.sender_name}
• Телефон: {order.sender_phone}

<b>🎁 Получатель:</b>
• Имя: {order.recipent_name or 'Не указано'}
• Телефон: {order.recipent_phone or 'Не указано'}

<b>🚚 Доставка:</b>
• Адрес: {full_address}
• Район: {district_display}
• Дата: {order.date}
• Время: {time_display}

<b>🛍️ Товары:</b>
{items_text}
"""

        if order.postcart:
            message += f"\n<b>💌 Текст открытки:</b>\n{order.postcart}\n"

        message += f"\n<i>Заказ создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}</i>"
        message += f"\n<i>Оплачен: {order.paid_at.strftime('%d.%m.%Y %H:%M') if order.paid_at else 'Не оплачен'}</i>"

        return message.strip()
