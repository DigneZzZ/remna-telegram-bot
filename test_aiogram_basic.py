#!/usr/bin/env python3
"""
Минимальный тест Aiogram бота без внешних зависимостей
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Mock admin user IDs для теста
MOCK_ADMIN_IDS = [123456789]  # Замените на ваш реальный Telegram ID

class AuthFilter:
    """Simple auth filter"""
    def __init__(self):
        pass
    
    def __call__(self) -> bool:
        return True  # Для теста разрешаем всем

async def start_handler(message: types.Message):
    """Handle /start command"""
    user_name = message.from_user.first_name or "Пользователь"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎛️ Главное меню", callback_data="main_menu"))
    builder.row(types.InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"))
    
    await message.answer(
        f"👋 Привет, {user_name}!\n\n"
        "🤖 Это тестовая версия Aiogram бота для Remnawave.\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )

async def callback_handler(callback: types.CallbackQuery):
    """Handle callback queries"""
    await callback.answer()
    
    if callback.data == "main_menu":
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="👥 Пользователи (тест)", callback_data="users"))
        builder.row(types.InlineKeyboardButton(text="🖥️ Серверы (тест)", callback_data="nodes"))
        builder.row(types.InlineKeyboardButton(text="📊 Статистика (тест)", callback_data="stats"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
        
        await callback.message.edit_text(
            "🎛️ **Главное меню**\n\n"
            "📊 **Статистика системы:**\n"
            "👥 Пользователи: Тест\n"
            "🖥️ Серверы: Тест\n\n"
            "Выберите раздел для управления:",
            reply_markup=builder.as_markup()
        )
    
    elif callback.data == "info":
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
        
        await callback.message.edit_text(
            "ℹ️ **Информация о боте**\n\n"
            "🤖 Версия: Aiogram Test\n"
            "📦 Библиотека: Aiogram 3.20.0\n"
            "🔧 Статус: Тестирование\n\n"
            "Этот бот успешно мигрирован с python-telegram-bot на Aiogram!",
            reply_markup=builder.as_markup()
        )
    
    elif callback.data in ["users", "nodes", "stats"]:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))
        
        section_names = {
            "users": "👥 Управление пользователями",
            "nodes": "🖥️ Управление серверами", 
            "stats": "📊 Статистика системы"
        }
        
        await callback.message.edit_text(
            f"{section_names[callback.data]}\n\n"
            "🚧 Этот раздел находится в разработке.\n"
            "Базовая функциональность Aiogram работает корректно!",
            reply_markup=builder.as_markup()
        )
    
    elif callback.data == "back":
        await start_handler(callback.message)

async def main():
    # Load environment variables
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен в .env файле")
        print("📝 Создайте .env файл на основе .env.example")
        return

    # Initialize bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    dp = Dispatcher()
    
    # Register handlers
    dp.message.register(start_handler, CommandStart())
    dp.callback_query.register(callback_handler)
    
    try:
        # Drop pending updates and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🚀 Запуск тестового Aiogram бота...")
        print("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main: {e}", exc_info=True)
