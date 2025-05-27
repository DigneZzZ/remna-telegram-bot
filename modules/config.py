import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging for config
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://remnawave:3000/api")
API_TOKEN = os.getenv("REMNAWAVE_API_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Parse admin user IDs with detailed logging
admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
logger.info(f"Raw ADMIN_USER_IDS from env: '{admin_ids_str}'")

ADMIN_USER_IDS = []
if admin_ids_str:
    try:
        ADMIN_USER_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        logger.info(f"Parsed ADMIN_USER_IDS: {ADMIN_USER_IDS}")
    except ValueError as e:
        logger.error(f"Error parsing ADMIN_USER_IDS: {e}")
        ADMIN_USER_IDS = []
else:
    logger.warning("ADMIN_USER_IDS is empty or not set!")

# Conversation states
MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU = range(6)
SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION = range(6, 9)
EDIT_USER, EDIT_FIELD, EDIT_VALUE = range(9, 12)
CREATE_USER, CREATE_USER_FIELD = range(12, 14)
BULK_MENU, BULK_ACTION, BULK_CONFIRM = range(14, 17)
EDIT_NODE, EDIT_NODE_FIELD = range(17, 19)
EDIT_HOST, EDIT_HOST_FIELD = range(19, 21)
CREATE_NODE, NODE_NAME, NODE_ADDRESS, NODE_PORT, NODE_TLS, SELECT_INBOUNDS = range(21, 27)

# User creation fields
USER_FIELDS = {
    'username': 'Имя пользователя',
    'trafficLimitBytes': 'Лимит трафика (в байтах)',
    'trafficLimitStrategy': 'Стратегия сброса трафика (NO_RESET, DAY, WEEK, MONTH)',
    'expireAt': 'Дата истечения (YYYY-MM-DD)',
    'description': 'Описание',
    'telegramId': 'Telegram ID',
    'email': 'Email',
    'tag': 'Тег',
    'hwidDeviceLimit': 'Лимит устройств'
}
# Dashboard display settings - что показывать на главном экране
DASHBOARD_SHOW_SYSTEM_STATS = os.getenv("DASHBOARD_SHOW_SYSTEM_STATS", "true").lower() == "true"
DASHBOARD_SHOW_SERVER_INFO = os.getenv("DASHBOARD_SHOW_SERVER_INFO", "true").lower() == "true"
DASHBOARD_SHOW_USERS_COUNT = os.getenv("DASHBOARD_SHOW_USERS_COUNT", "true").lower() == "true"
DASHBOARD_SHOW_NODES_COUNT = os.getenv("DASHBOARD_SHOW_NODES_COUNT", "true").lower() == "true"
DASHBOARD_SHOW_TRAFFIC_STATS = os.getenv("DASHBOARD_SHOW_TRAFFIC_STATS", "true").lower() == "true"
DASHBOARD_SHOW_UPTIME = os.getenv("DASHBOARD_SHOW_UPTIME", "true").lower() == "true"

# Настройки поиска пользователей
ENABLE_PARTIAL_SEARCH = os.getenv("ENABLE_PARTIAL_SEARCH", "true").lower() == "true"
SEARCH_MIN_LENGTH = int(os.getenv("SEARCH_MIN_LENGTH", "2"))