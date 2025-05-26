from functools import wraps
from modules.config import ADMIN_USER_IDS
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

def check_admin(func):
    """Decorator to check if user is admin"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_USER_IDS:
            await update.message.reply_text("⛔ Вы не авторизованы для использования этого бота.")
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapped
