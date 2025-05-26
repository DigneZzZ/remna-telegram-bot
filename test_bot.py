#!/usr/bin/env python3
"""
Simple bot test to check if everything works
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Start command handler"""
    user = update.effective_user
    logger.info(f"Start command from user: {user.id} (@{user.username}, {user.first_name})")
    
    message = f"""
🤖 Bot Test

👤 User Info:
- ID: {user.id}
- Username: @{user.username or 'No username'}
- First Name: {user.first_name or 'No name'}
- Last Name: {user.last_name or 'No last name'}

✅ Bot is working correctly!
"""
    await update.message.reply_text(message)

async def echo(update, context):
    """Echo all messages"""
    user = update.effective_user
    logger.info(f"Message from user {user.id}: {update.message.text}")
    await update.message.reply_text(f"Echo: {update.message.text}")

async def main():
    """Main function"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        return

    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("Starting test bot...")
    
    try:
        await application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Test bot stopped!")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
