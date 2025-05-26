from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU, BULK_MENU
from modules.handlers.user_handlers import show_users_menu, start_create_user
from modules.handlers.node_handlers import show_nodes_menu
from modules.handlers.stats_handlers import show_stats_menu
from modules.handlers.host_handlers import show_hosts_menu
from modules.handlers.inbound_handlers import show_inbounds_menu
from modules.handlers.bulk_handlers import show_bulk_menu

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data="users")],
        [InlineKeyboardButton("🖥️ Серверы", callback_data="nodes")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🌐 Хосты", callback_data="hosts")],
        [InlineKeyboardButton("📡 Входящие соединения", callback_data="inbounds")],
        [InlineKeyboardButton("🔄 Массовые операции", callback_data="bulk")],
        [InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🤖 *Remnawave Admin Bot*\n\n"
    message += "Выберите раздел:"

    if update.callback_query:
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

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "users" or data == "menu_users":
        await show_users_menu(update, context)
        return USER_MENU

    elif data == "nodes" or data == "menu_nodes":
        await show_nodes_menu(update, context)
        return NODE_MENU

    elif data == "stats" or data == "menu_stats":
        await show_stats_menu(update, context)
        return STATS_MENU

    elif data == "hosts" or data == "menu_hosts":
        await show_hosts_menu(update, context)
        return HOST_MENU

    elif data == "inbounds" or data == "menu_inbounds":
        await show_inbounds_menu(update, context)
        return INBOUND_MENU

    elif data == "bulk" or data == "menu_bulk":
        await show_bulk_menu(update, context)
        return BULK_MENU

    elif data == "create_user" or data == "menu_create_user":
        await start_create_user(update, context)
        return USER_MENU

    return MAIN_MENU
