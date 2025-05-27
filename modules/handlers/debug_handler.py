"""
Debug handler to log all incoming messages and updates
"""
from aiogram import types
import logging

logger = logging.getLogger(__name__)

async def debug_message_handler(message: types.Message):
    """Log all incoming messages for debugging"""
    user = message.from_user
    if user:
        logger.info(f"📨 Received message from user: {user.id} (@{user.username}, {user.first_name})")
    
    logger.info(f"💬 Message: '{message.text}' (chat_id: {message.chat.id})")
    if message.text and message.text.startswith('/'):
        logger.info(f"🎯 Command detected: {message.text}")
    
    logger.info(f"📋 Message details: {message}")

async def debug_callback_handler(callback_query: types.CallbackQuery):
    """Log all callback queries for debugging"""
    user = callback_query.from_user
    if user:
        logger.info(f"📨 Received callback from user: {user.id} (@{user.username}, {user.first_name})")
    
    logger.info(f"🔘 Callback query: {callback_query.data}")
    logger.info(f"📋 Callback details: {callback_query}")
    
    # Don't handle the callback, just log it
