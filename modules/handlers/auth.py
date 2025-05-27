from aiogram import types
from aiogram.filters import Filter
import logging

from modules.config import ADMIN_USER_IDS

logger = logging.getLogger(__name__)

class AuthFilter(Filter):
    """Filter to check if user is authorized"""
    
    async def __call__(self, message_or_callback: types.Message | types.CallbackQuery) -> bool:
        if isinstance(message_or_callback, types.Message):
            user = message_or_callback.from_user
        elif isinstance(message_or_callback, types.CallbackQuery):
            user = message_or_callback.from_user
        else:
            return False
            
        user_id = user.id
        username = user.username or "Unknown"
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            
            # Send unauthorized message
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.answer(
                    "❌ Доступ запрещен.\n\n"
                    "Этот бот предназначен только для авторизованных пользователей.\n"
                    f"Ваш ID: {user_id}\n"
                    f"Username: @{username}"
                )
            elif isinstance(message_or_callback, types.CallbackQuery):
                await message_or_callback.answer(
                    "❌ Доступ запрещен",
                    show_alert=True
                )
            
            return False
        
        return True

def check_authorization(user: types.User) -> bool:
    """Check if user is authorized"""
    return user.id in ADMIN_USER_IDS
