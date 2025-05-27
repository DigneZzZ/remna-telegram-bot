import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters

# Import modules
from modules.handlers.conversation_handler import create_conversation_handler

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
    
    # Configure telegram library logging
    # For production (ERROR), disable telegram debug logs
    # For development (DEBUG/INFO), allow telegram logs
    if level <= logging.INFO:
        logging.getLogger('telegram').setLevel(logging.INFO)
        logging.getLogger('telegram.ext').setLevel(logging.INFO)
    else:
        logging.getLogger('telegram').setLevel(logging.ERROR)
        logging.getLogger('telegram.ext').setLevel(logging.ERROR)
    
    return level

# Setup logging
current_log_level = setup_logging()
logger = logging.getLogger(__name__)

def main():
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
      # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Create and add conversation handler
    conv_handler = create_conversation_handler()
    application.add_handler(conv_handler, group=0)
    
    try:
        # Run polling - production configuration
        application.run_polling(
            poll_interval=2.0,
            timeout=15,
            bootstrap_retries=3,
            read_timeout=15,
            write_timeout=15,
            connect_timeout=15,
            pool_timeout=15,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Critical error during polling: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass  # Graceful shutdown
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
