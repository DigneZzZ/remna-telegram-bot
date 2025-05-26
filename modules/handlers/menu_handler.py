from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from modules.config import MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU, BULK_MENU, CREATE_USER, CREATE_USER_FIELD, SELECTING_USER
from modules.utils.auth import check_authorization
from modules.handlers.user_handlers import show_users_menu, start_create_user, show_user_details
from modules.handlers.node_handlers import show_nodes_menu
from modules.handlers.stats_handlers import show_stats_menu
from modules.handlers.host_handlers import show_hosts_menu
from modules.handlers.inbound_handlers import show_inbounds_menu
from modules.handlers.bulk_handlers import show_bulk_menu
from modules.handlers.start_handler import show_main_menu

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selection"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
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
        return CREATE_USER_FIELD

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU

    elif data.startswith("view_"):
        uuid = data.split("_")[1]
        await show_user_details(update, context, uuid)
        return SELECTING_USER

    return MAIN_MENU

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu with authorization check"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    # Показываем главное меню со статистикой
    await show_main_menu(update, context)
    return MAIN_MENU
