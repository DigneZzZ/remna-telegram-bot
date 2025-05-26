import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application

# Import modules
from modules.handlers.conversation_handler import create_conversation_handler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    api_token = os.getenv("REMNAWAVE_API_TOKEN")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_user_ids = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id]
    
    if not api_token:
        logger.error("REMNAWAVE_API_TOKEN environment variable is not set")
        return

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        return

    if not admin_user_ids:
        logger.warning("ADMIN_USER_IDS environment variable is not set. No users will be able to use the bot.")
    
    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Create and add conversation handler
    conv_handler = create_conversation_handler()
    application.add_handler(conv_handler)
    
    # Start the Bot
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
