#!/usr/bin/env python3
"""
Simple test bot to get Telegram user ID
This is a minimal bot that will respond with user's Telegram ID
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message and return user ID"""
    user = update.effective_user
    chat = update.effective_chat
    
    response = f"🆔 **Ваша информация:**\n\n"
    response += f"👤 User ID: `{user.id}`\n"
    response += f"📝 Username: @{user.username or 'Не установлен'}\n"
    response += f"👋 Имя: {user.first_name or 'Не установлено'}\n"
    response += f"👨‍👩‍👧‍👦 Фамилия: {user.last_name or 'Не установлена'}\n"
    response += f"💬 Chat ID: `{chat.id}`\n"
    response += f"📱 Chat Type: {chat.type}\n\n"
    response += f"📋 **Для настройки бота:**\n"
    response += f"Добавьте `{user.id}` в ADMIN_USER_IDS в файле .env"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await get_id_handler(update, context)

def main():
    """Main function"""
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_id_handler))
    
    logger.info("🤖 ID Bot запущен! Отправьте любое сообщение для получения вашего ID")
    
    # Start polling
    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 ID Bot остановлен!")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
