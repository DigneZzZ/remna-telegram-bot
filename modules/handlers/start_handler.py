from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from modules.config import MAIN_MENU
from modules.utils.auth import check_admin
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.api.inbounds import InboundAPI
import logging

logger = logging.getLogger(__name__)

@check_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu with system statistics"""
    keyboard = [
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="users")],
        [InlineKeyboardButton("🖥️ Управление серверами", callback_data="nodes")],
        [InlineKeyboardButton("📊 Статистика системы", callback_data="stats")],
        [InlineKeyboardButton("🌐 Управление хостами", callback_data="hosts")],
        [InlineKeyboardButton("🔌 Управление Inbounds", callback_data="inbounds")],
        [InlineKeyboardButton("🔄 Массовые операции", callback_data="bulk")],
        [InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем статистику системы
    stats_text = await get_system_stats()
    
    message = "🎛️ *Главное меню Remnawave Admin*\n\n"
    message += stats_text + "\n"
    message += "Выберите раздел для управления:"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def get_system_stats():
    """Get basic system statistics"""
    try:
        # Получаем статистику пользователей
        users_response = await UserAPI.get_all_users()
        users_count = 0
        active_users = 0
        if users_response:
            # Проверяем разные возможные структуры ответа
            users = []
            if isinstance(users_response, dict):
                if 'users' in users_response:
                    users = users_response['users']
                elif 'response' in users_response and 'users' in users_response['response']:
                    users = users_response['response']['users']
            elif isinstance(users_response, list):
                users = users_response
            
            users_count = len(users)
            active_users = sum(1 for user in users if user.get('status') == 'ACTIVE')

        # Получаем статистику узлов
        nodes_response = await NodeAPI.get_all_nodes()
        nodes_count = 0
        online_nodes = 0
        if nodes_response:
            # Проверяем разные возможные структуры ответа
            nodes = []
            if isinstance(nodes_response, dict):
                if 'nodes' in nodes_response:
                    nodes = nodes_response['nodes']
                elif 'response' in nodes_response and 'nodes' in nodes_response['response']:
                    nodes = nodes_response['response']['nodes']
            elif isinstance(nodes_response, list):
                nodes = nodes_response
            
            nodes_count = len(nodes)
            online_nodes = sum(1 for node in nodes if node.get('isConnected'))

        # Получаем статистику inbound'ов
        inbounds_response = await InboundAPI.get_all_inbounds()
        inbounds_count = 0
        if inbounds_response:
            # Проверяем разные возможные структуры ответа
            inbounds = []
            if isinstance(inbounds_response, dict):
                if 'inbounds' in inbounds_response:
                    inbounds = inbounds_response['inbounds']
                elif 'response' in inbounds_response and 'inbounds' in inbounds_response['response']:
                    inbounds = inbounds_response['response']['inbounds']
            elif isinstance(inbounds_response, list):
                inbounds = inbounds_response
            
            inbounds_count = len(inbounds)

        # Формируем текст статистики
        stats = f"📈 *Общая статистика системы:*\n"
        stats += f"👥 Пользователи: {active_users}/{users_count}\n"
        stats += f"🖥️ Узлы: {online_nodes}/{nodes_count} онлайн\n"
        stats += f"🔌 Inbound'ы: {inbounds_count} шт.\n"
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return "📈 *Статистика временно недоступна*\n"
