#!/usr/bin/env python3
"""
Скрипт для изменения статуса pending заказов на paid
И отправки уведомлений в Telegram
"""

import os
import sys
import django

# ВАЖНО: Измените этот путь на свой!
sys.path.insert(0, '/users/mykon/PycharmProjects/floricraft')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FloriCraft.settings')
django.setup()

from apps.orders.models import Order
from apps.orders.telegram_service import TelegramNotificationService
from django.utils import timezone

print("\n" + "=" * 80)
print("ОБНОВЛЕНИЕ PENDING ЗАКАЗОВ → PAID + ОТПРАВКА УВЕДОМЛЕНИЙ")
print("=" * 80 + "\n")

# Получаем pending заказы
pending_orders = Order.objects.filter(status='pending').order_by('-created_at')

if not pending_orders.exists():
    print("✅ Нет заказов со статусом 'pending'")
    print("   Все заказы уже обработаны!")
    sys.exit(0)

print(f"📦 Найдено заказов: {pending_orders.count()}\n")

# Показываем список
for i, order in enumerate(pending_orders, 1):
    print(f"{i}. Заказ #{order.id}")
    print(f"   Получатель: {order.recipent_name}")
    print(f"   Сумма: {order.total_amount} ₽")
    print(f"   Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}")
    print()

# Подтверждение
print("-" * 80)
answer = input("Обновить эти заказы и отправить уведомления? (да/нет): ").strip().lower()

if answer not in ['да', 'yes', 'y', 'д']:
    print("❌ Отменено")
    sys.exit(0)

print("\n" + "=" * 80)
print("ОБРАБОТКА ЗАКАЗОВ")
print("=" * 80 + "\n")

# Инициализируем сервис уведомлений
telegram_service = TelegramNotificationService()

success = 0
notifications_sent = 0
errors = []

for order in pending_orders:
    print(f"Обработка заказа #{order.id}...")
    
    try:
        # 1. Обновляем статус
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'paid_at'])
        print(f"  ✅ Статус изменен на 'paid'")
        success += 1
        
        # 2. Отправляем уведомление
        try:
            result = telegram_service.send_new_order_notification(order)
            if result:
                print(f"  ✅ Уведомление отправлено в Telegram")
                notifications_sent += 1
            else:
                print(f"  ⚠️  Статус обновлен, но уведомление не отправлено")
                errors.append(f"Заказ #{order.id}: уведомление не отправлено")
        except Exception as e:
            print(f"  ❌ Ошибка отправки уведомления: {str(e)}")
            errors.append(f"Заказ #{order.id}: {str(e)}")
        
        print()
        
    except Exception as e:
        print(f"  ❌ Ошибка обновления заказа: {str(e)}")
        errors.append(f"Заказ #{order.id}: {str(e)}")
        print()

# Итоги
print("=" * 80)
print("РЕЗУЛЬТАТЫ")
print("=" * 80)
print(f"✅ Заказов обновлено: {success}/{pending_orders.count()}")
print(f"📱 Уведомлений отправлено: {notifications_sent}/{success}")

if errors:
    print(f"\n⚠️  Ошибки ({len(errors)}):")
    for error in errors:
        print(f"   • {error}")
else:
    print("\n🎉 Все заказы успешно обработаны!")

print("\n" + "=" * 80)

if notifications_sent > 0:
    print("\n✅ ГОТОВО! Проверьте:")
    print("   1. Telegram бот - должны прийти уведомления")
    print("   2. Команда /orders - должны отобразиться заказы")
    print()
elif success > 0:
    print("\n⚠️  Заказы обновлены, но уведомления не отправлены.")
    print("   Возможные причины:")
    print("   1. Нет активных администраторов (выполните /start в боте)")
    print("   2. TELEGRAM_BOT_TOKEN не настроен")
    print("   3. Проблема с Telegram API")
    print()
    print("   Запустите diagnostic_script.py для диагностики")
    print()