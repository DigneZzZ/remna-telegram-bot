"""
Debug handler to log all incoming messages and updates
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log all incoming updates for debugging"""
    user = update.effective_user
    if user:
        logger.info(f"📨 Received update from user: {user.id} (@{user.username}, {user.first_name})")
    
    if update.message:
        logger.info(f"💬 Message: '{update.message.text}' (chat_id: {update.message.chat_id})")
        if update.message.text and update.message.text.startswith('/'):
            logger.info(f"🎯 Command detected: {update.message.text}")
    elif update.callback_query:
        logger.info(f"🔘 Callback query: {update.callback_query.data}")
    else:
        logger.info(f"🔍 Other update type: {type(update)}")
    
    logger.info(f"📋 Update details: {update}")
    
    # Don't handle the update, just log it
    return
