from functools import wraps
from modules.config import ADMIN_USER_IDS
from modules.api.sdk_client import get_remnawave_sdk
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
    """Check if remnawave API is accessible"""
    try:
        sdk = get_remnawave_sdk()
        response = await sdk.users.get_all_users(start=0, size=1000)
        logger.info(f"Remnawave API connection successful. Total users: {response.total}")
        return True
    except Exception as e:
        logger.error(f"Remnawave API connection failed: {e}")
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
