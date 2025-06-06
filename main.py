import asyncio
import os
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Import modules
from modules.config import ADMIN_USER_IDS
from modules.handlers import register_all_handlers

def setup_logging():
    """Setup logging configuration from environment variables"""
    # Load environment variables first
    load_dotenv()
    
    # Get log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
    
    # Map string log levels to logging constants
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # Set the log level, default to ERROR if invalid level provided
    level = log_levels.get(log_level, logging.ERROR)
    
    # Configure basic logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level,
        force=True  # Override any existing logging configuration
    )
    
    # Configure aiogram library logging
    # For production (ERROR), disable aiogram debug logs
    # For development (DEBUG/INFO), allow aiogram logs
    if level <= logging.INFO:
        logging.getLogger('aiogram').setLevel(logging.INFO)
    else:
        logging.getLogger('aiogram').setLevel(logging.ERROR)
    
    return level

# Setup logging
current_log_level = setup_logging()
logger = logging.getLogger(__name__)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    api_token = os.getenv("REMNAWAVE_API_TOKEN")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_user_ids = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id]
    
    # Environment check - only errors in production
    if not api_token:
        logger.error("REMNAWAVE_API_TOKEN environment variable is not set")
        return

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        return

    if not admin_user_ids:
        logger.error("ADMIN_USER_IDS environment variable is not set. No users will be able to use the bot.")
        return
      # Initialize bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
      # Register all handlers
    register_all_handlers(dp)
    
    try:
        # Drop pending updates and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error during polling: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
