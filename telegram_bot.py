"""
Telegram бот для уведомлений о заказах FloriCraft
Использует aiogram 3.x
"""

import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DJANGO_API_URL = os.getenv('DJANGO_API_URL')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле!")

if not DJANGO_API_URL:
    raise ValueError("DJANGO_API_URL не найден в .env файле! Укажите URL вашего Django сервера (например: https://ваш-проект.onrender.com)")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    Регистрирует администратора в Django
    """
    user = message.from_user
    chat_id = message.chat.id

    logger.info(f"Получена команда /start от пользователя {chat_id} (@{user.username})")

    # Отправляем данные администратора в Django
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/api/orders/telegram/register/",
            json={
                "chat_id": chat_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            action = "зарегистрированы" if data.get('action') == 'registered' else "обновлены"

            await message.answer(
                f"✅ <b>Добро пожаловать!</b>\n\n"
                f"Вы успешно {action} как администратор FloriCraft.\n\n"
                f"📋 <b>Ваши данные:</b>\n"
                f"• Chat ID: <code>{chat_id}</code>\n"
                f"• Username: @{user.username or 'не указан'}\n"
                f"• Имя: {user.first_name or 'не указано'}\n\n"
                f"🔔 Теперь вам будут приходить уведомления о всех новых заказах!\n\n"
                f"Используйте /help для просмотра доступных команд.",
                parse_mode="HTML"
            )
            logger.info(f"Администратор {chat_id} успешно зарегистрирован")
        else:
            await message.answer(
                "❌ Ошибка регистрации. Попробуйте позже или обратитесь к разработчику.",
                parse_mode="HTML"
            )
            logger.error(f"Ошибка регистрации администратора: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        await message.answer(
            "❌ Не удалось связаться с сервером. Убедитесь, что Django сервер запущен.",
            parse_mode="HTML"
        )
        logger.error(f"Ошибка подключения к Django API: {str(e)}")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📋 <b>FloriCraft Notifications Bot</b>\n\n"
        "<b>Доступные команды:</b>\n\n"
        "/start - Регистрация как администратор\n"
        "/help - Показать эту справку\n"
        "/status - Проверить статус регистрации\n"
        "/chatid - Узнать свой Chat ID\n\n"
        "🔔 Уведомления о новых оплаченных заказах приходят автоматически!",
        parse_mode="HTML"
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Проверить статус регистрации администратора"""
    user = message.from_user
    await message.answer(
        f"📊 <b>Ваш статус:</b>\n\n"
        f"• Chat ID: <code>{message.chat.id}</code>\n"
        f"• Username: @{user.username or 'не указан'}\n"
        f"• Имя: {user.first_name or 'не указано'}\n\n"
        f"Если вы зарегистрированы, уведомления будут приходить автоматически.\n"
        f"Для регистрации используйте команду /start",
        parse_mode="HTML"
    )


@dp.message(Command("chatid"))
async def cmd_chatid(message: Message):
    """Показать Chat ID пользователя"""
    await message.answer(
        f"🆔 <b>Ваш Chat ID:</b> <code>{message.chat.id}</code>\n\n"
        f"Скопируйте его, если нужно добавить вручную в базу данных.",
        parse_mode="HTML"
    )


@dp.message()
async def echo_handler(message: Message):
    """
    Обработчик всех остальных сообщений
    """
    await message.answer(
        "👋 Я бот для уведомлений о заказах FloriCraft.\n\n"
        "Используйте /help для просмотра доступных команд.",
        parse_mode="HTML"
    )


async def main():
    """Запуск бота"""
    logger.info("🚀 Бот запускается...")
    logger.info(f"📡 Django API URL: {DJANGO_API_URL}")

    try:
        # Удаляем старые webhook если есть
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Бот успешно запущен и готов к работе!")

        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {str(e)}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
