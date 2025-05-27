from aiogram import Router, types
from aiogram.filters import CommandStart
import logging

from modules.handlers_aiogram.auth import AuthFilter

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart(), AuthFilter())
async def start_command(message: types.Message):
    """Start command handler"""
    from modules.handlers_aiogram.menu_handler import show_main_menu
    
    user_name = message.from_user.first_name or "Пользователь"
    welcome_text = f"👋 Привет, {user_name}!\n\n🤖 Это бот для управления Remnawave.\n\nВыберите действие из меню ниже:"
    
    await show_main_menu(message, welcome_text)

def register_start_handlers(dp):
    """Register start handlers"""
    dp.include_router(router)
