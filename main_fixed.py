import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters

# Import modules
from modules.handlers.conversation_handler import create_conversation_handler
from modules.handlers.debug_handler import debug_handler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Enable more detailed telegram logging
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('telegram.ext').setLevel(logging.DEBUG)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    api_token = os.getenv("REMNAWAVE_API_TOKEN")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_user_ids = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id]
    
    logger.info(f"Environment check:")
    logger.info(f"- API token configured: {'Yes' if api_token else 'No'}")
    logger.info(f"- Bot token configured: {'Yes' if bot_token else 'No'}")
    logger.info(f"- Admin user IDs: {admin_user_ids}")
    
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
    
    # Add debug handlers first (lower priority)
    application.add_handler(MessageHandler(filters.ALL, debug_handler), group=1)
    application.add_handler(CallbackQueryHandler(debug_handler), group=1)
    
    # Create and add conversation handler (higher priority)
    conv_handler = create_conversation_handler()
    application.add_handler(conv_handler, group=0)
    
    logger.info("Conversation handler added successfully")
    logger.info("Starting bot with polling...")
    
    try:
        # Run polling - this handles initialization and start automatically
        await application.run_polling(
            poll_interval=1.0,
            timeout=10,
            bootstrap_retries=5,
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=10,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
