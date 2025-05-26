from functools import wraps
from modules.config import ADMIN_USER_IDS
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging

logger = logging.getLogger(__name__)

def check_admin(func):
    """Decorator to check if user is admin"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        first_name = update.effective_user.first_name or "Unknown"
        
        logger.info(f"Authorization check for user: {user_id} (@{username}, {first_name})")
        logger.info(f"Configured admin IDs: {ADMIN_USER_IDS}")
        
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            if update.message:
                await update.message.reply_text("⛔ Вы не авторизованы для использования этого бота.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
            return ConversationHandler.END
        
        logger.info(f"User {user_id} (@{username}) authorized successfully")
        return await func(update, context, *args, **kwargs)
    return wrapped

def check_authorization(user):
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
