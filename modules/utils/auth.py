from functools import wraps
from modules.config import ADMIN_USER_IDS
from modules.api.client import RemnaAPI
from modules.api.users import get_all_users
from aiogram import types
from aiogram.fsm.context import FSMContext
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
        # Используем прямой HTTP вызов вместо SDK
        users_data = await get_all_users()
        
        if users_data is not None:
            users_count = len(users_data) if isinstance(users_data, list) else 0
            logger.info(f"Remnawave API connection successful. Total users: {users_count}")
            return True
        else:
            logger.warning("Remnawave API returned no data")
            return False
            
    except Exception as e:
        logger.error(f"Remnawave API connection failed: {e}")
        return False

async def check_remnawave_connection_basic():
    """Basic connection check using HTTP client"""
    try:
        # Альтернативный способ проверки через прямой HTTP клиент
        api_client = RemnaAPI()
        
        # Простой тест соединения - получаем системную информацию
        result = await api_client.get("system/stats")
        
        if result:
            logger.info("Remnawave API basic connection successful")
            return True
        else:
            logger.warning("Remnawave API basic connection failed - no response")
            return False
            
    except Exception as e:
        logger.error(f"Remnawave API basic connection failed: {e}")
        return False

def require_remnawave_connection(func):
    """Decorator to check if remnawave API is accessible before executing function"""
    @wraps(func)
    async def wrapped(message: types.Message, *args, **kwargs):
        if not await check_remnawave_connection():
            await message.answer("❌ Панель RemnaWave недоступна. Попробуйте позже.")
            return
        
        return await func(message, *args, **kwargs)
    return wrapped

def require_remnawave_connection_callback(func):
    """Decorator to check if remnawave API is accessible for callback queries"""
    @wraps(func)
    async def wrapped(callback: types.CallbackQuery, *args, **kwargs):
        if not await check_remnawave_connection():
            await callback.answer("❌ Панель RemnaWave недоступна. Попробуйте позже.", show_alert=True)
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
            await message.answer("❌ Панель RemnaWave недоступна. Попробуйте позже.")
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
            await callback.answer("❌ Панель RemnaWave недоступна. Попробуйте позже.", show_alert=True)
            return
        
        return await func(callback, *args, **kwargs)
    return wrapped

# Добавляем универсальную функцию для быстрой проверки API
async def is_api_available():
    """Quick API availability check"""
    try:
        # Простая проверка доступности API
        api_client = RemnaAPI()
        
        # Пытаемся получить минимум данных для проверки
        result = await api_client.get("system/stats")
        return result is not None
        
    except Exception as e:
        logger.debug(f"API availability check failed: {e}")
        return False

logger.info("Auth module loaded successfully (SDK-free version)")