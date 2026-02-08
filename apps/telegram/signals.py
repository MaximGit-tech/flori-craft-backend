"""
Signals для автоматической отправки уведомлений о заказах
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.orders.telegram_service import TelegramNotificationService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    """
    Отправляет уведомление в Telegram при создании нового оплаченного заказа
    или при изменении статуса на 'paid'
    """
    if instance.status == 'paid':
        if created or (not created and instance.paid_at):
            try:
                service = TelegramNotificationService()
                success = service.send_new_order_notification(instance)
                
                if success:
                    logger.info(f"✅ Уведомление о заказе #{instance.id} отправлено в Telegram")
                else:
                    logger.warning(f"⚠️ Не удалось отправить уведомление о заказе #{instance.id}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке уведомления о заказе #{instance.id}: {str(e)}")

@receiver(post_save, sender=Order)
def send_order_notification_on_status_change(sender, instance, created, **kwargs):
    """
    Отправляет уведомление только при изменении статуса заказа на 'paid'
    Используйте этот сигнал вместо предыдущего, если нужна более точная логика
    """
    pass
