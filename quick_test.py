#!/usr/bin/env python3
"""
Quick test script to verify bot is working
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

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
    logger.info(f"✅ Bot responded to user: {user.id} (@{user.username})")
    
    await update.message.reply_text(
        f"🤖 **Bot Test Successful!**\n\n"
        f"👤 **User Info:**\n"
        f"• ID: `{user.id}`\n"
        f"• Username: @{user.username or 'No username'}\n"
        f"• Name: {user.first_name or 'No name'}\n\n"
        f"✅ Bot is working correctly!",
        parse_mode="Markdown"
    )

async def main():
    """Main function"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN environment variable is not set")
        return

    logger.info(f"🚀 Starting quick test bot...")
    
    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    
    logger.info("✅ Test bot ready - send /start to test")
    
    try:
        await application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Test bot stopped!")
    except Exception as e:
        logger.error(f"❌ Error in main: {e}", exc_info=True)
