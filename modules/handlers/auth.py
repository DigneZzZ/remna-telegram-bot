from functools import wraps
from modules.config import ADMIN_USER_IDS
from modules.api.client import RemnaAPI
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters import BaseFilter
import logging

logger = logging.getLogger(__name__)

def check_admin(func):
    """Decorator to check if user is admin"""
    @wraps(func)
    async def wrapped(message: types.Message, *args, **kwargs):
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        first_name = message.from_user.first_name or "Unknown"
        
        logger.info(f"Authorization check for user: {user_id} (@{username}, {first_name})")
        logger.info(f"Configured admin IDs: {ADMIN_USER_IDS}")
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            await message.answer("⛔ Вы не авторизованы для использования этого бота.")
            return
        
        logger.info(f"User {user_id} (@{username}) authorized successfully")
        return await func(message, *args, **kwargs)
    return wrapped

def check_admin_callback(func):
    """Decorator to check if user is admin for callback queries"""
    @wraps(func)
    async def wrapped(callback: types.CallbackQuery, *args, **kwargs):
        user_id = callback.from_user.id
        username = callback.from_user.username or "Unknown"
        first_name = callback.from_user.first_name or "Unknown"
        
        logger.info(f"Authorization check for user: {user_id} (@{username}, {first_name})")
        logger.info(f"Configured admin IDs: {ADMIN_USER_IDS}")
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            await callback.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
            return
        
        logger.info(f"User {user_id} (@{username}) authorized successfully")
        return await func(callback, *args, **kwargs)
    return wrapped

def check_authorization(user: types.User):
    """Check if user is authorized (without decorator)"""
    user_id = user.id
    username = user.username or "Unknown"
    first_name = user.first_name or "Unknown"
    
    logger.info(f"Authorization check for user: {user_id} (@{username}, {first_name})")
    logger.info(f"Configured admin IDs: {ADMIN_USER_IDS}")
    
    if user_id not in ADMIN_USER_IDS:
        logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
        return False
    
    logger.info(f"User {user_id} (@{username}) authorized successfully")
    return True

async def check_remnawave_connection():
    """Check if remnawave API is accessible using direct HTTP calls"""
    try:
        logger.debug("Checking Remnawave API connection...")
        
        # Пробуем разные endpoints для проверки доступности API
        test_endpoints = [
            ("users", {"size": 1}),  # Простой запрос пользователей
            ("nodes", None),         # Получить ноды
            ("system/stats", None),  # Системная статистика
            ("hosts", None)          # Хосты
        ]
        
        for endpoint, params in test_endpoints:
            try:
                logger.debug(f"Testing API endpoint: {endpoint}")
                response = await RemnaAPI.get(endpoint, params)
                
                if response is not None:
                    logger.info(f"Remnawave API connection successful via {endpoint}")
                    return True
                else:
                    logger.debug(f"Endpoint {endpoint} returned None")
                    
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {e}")
                continue
        
        logger.warning("All API endpoints failed")
        return False
        
    except Exception as e:
        logger.error(f"Remnawave API connection check failed: {e}")
        return False

def require_remnawave_connection(func):
    """Decorator to check if remnawave API is accessible before executing function"""
    @wraps(func)
    async def wrapped(message: types.Message, *args, **kwargs):
        if not await check_remnawave_connection():
            await message.answer("❌ Панель RemнаWave недоступна. Попробуйте позже.")
            return
        
        return await func(message, *args, **kwargs)
    return wrapped

def require_remnawave_connection_callback(func):
    """Decorator to check if remnawave API is accessible for callback queries"""
    @wraps(func)
    async def wrapped(callback: types.CallbackQuery, *args, **kwargs):
        if not await check_remnawave_connection():
            await callback.answer("❌ Панель RemнаWave недоступна. Попробуйте позже.", show_alert=True)
            return
        
        return await func(callback, *args, **kwargs)
    return wrapped

def admin_and_remnawave_required(func):
    """Combined decorator for admin check and remnawave connection check"""
    @wraps(func)
    async def wrapped(message: types.Message, *args, **kwargs):
        # Проверяем админа
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        first_name = message.from_user.first_name or "Unknown"
        
        logger.info(f"Authorization check for user: {user_id} (@{username}, {first_name})")
        logger.info(f"Configured admin IDs: {ADMIN_USER_IDS}")
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            await message.answer("⛔ Вы не авторизованы для использования этого бота.")
            return
        
        logger.info(f"User {user_id} (@{username}) authorized successfully")
        
        # Проверяем соединение с RemnaWave
        if not await check_remnawave_connection():
            await message.answer("❌ Панель RemнаWave недоступна. Попробуйте позже.")
            return
        
        return await func(message, *args, **kwargs)
    return wrapped

def admin_and_remnawave_required_callback(func):
    """Combined decorator for callback queries"""
    @wraps(func)
    async def wrapped(callback: types.CallbackQuery, *args, **kwargs):
        # Проверяем админа
        user_id = callback.from_user.id
        username = callback.from_user.username or "Unknown"
        first_name = callback.from_user.first_name or "Unknown"
        
        logger.info(f"Authorization check for user: {user_id} (@{username}, {first_name})")
        logger.info(f"Configured admin IDs: {ADMIN_USER_IDS}")
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            await callback.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
            return
        
        logger.info(f"User {user_id} (@{username}) authorized successfully")
        
        # Проверяем соединение с RemnaWave
        if not await check_remnawave_connection():
            await callback.answer("❌ Панель RemнаWave недоступна. Попробуйте позже.", show_alert=True)
            return
        
        return await func(callback, *args, **kwargs)
    return wrapped

class AuthFilter(BaseFilter):
    """Filter for admin authorization and remnawave connection check"""
    
    async def __call__(self, obj: types.TelegramObject) -> bool:
        # Определяем тип объекта и извлекаем пользователя
        if isinstance(obj, types.Message):
            user = obj.from_user
        elif isinstance(obj, types.CallbackQuery):
            user = obj.from_user
        else:
            return False
        
        # Проверяем авторизацию
        user_id = user.id
        username = user.username or "Unknown"
        
        logger.info(f"AuthFilter: checking user {user_id} (@{username})")
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"AuthFilter: unauthorized access attempt from user {user_id} (@{username})")
            return False
        
        # Проверяем соединение с RemnaWave
        try:
            if not await check_remnawave_connection():
                logger.warning("AuthFilter: RemnaWave connection failed")
                return False
        except Exception as e:
            logger.error(f"AuthFilter: Error checking RemnaWave connection: {e}")
            return False
        
        logger.info(f"AuthFilter: user {user_id} (@{username}) authorized successfully")
        return True

# Вспомогательные функции для быстрых проверок
async def quick_api_check() -> bool:
    """Quick API availability check"""
    try:
        result = await RemnaAPI.get("users", params={"size": 1})
        return result is not None
    except Exception:
        return False

def is_admin(user_id: int) -> bool:
    """Simple admin check"""
    return user_id in ADMIN_USER_IDS

async def validate_api_and_admin(user_id: int) -> tuple[bool, str]:
    """Validate both admin status and API availability
    
    Returns:
        tuple[bool, str]: (success, error_message)
    """
    if not is_admin(user_id):
        return False, "⛔ Вы не авторизованы для использования этого бота."
    
    if not await quick_api_check():
        return False, "❌ Панель RemнаWave недоступна. Попробуйте позже."
    
    return True, ""