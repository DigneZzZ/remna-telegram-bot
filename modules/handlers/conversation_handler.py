from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ConversationHandler
)
from telegram import Update
from telegram.ext import ContextTypes
import logging

from modules.config import (
    MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU, BULK_MENU,
    SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION,
    EDIT_USER, EDIT_FIELD, EDIT_VALUE,
    CREATE_USER, CREATE_USER_FIELD, BULK_CONFIRM, ADMIN_USER_IDS
)

from modules.handlers.start_handler import start
from modules.handlers.menu_handler import handle_menu_selection
from modules.handlers.user_handlers import (
    handle_users_menu, handle_user_selection, handle_user_action,
    handle_action_confirmation, handle_text_input,
    handle_edit_field_selection, handle_edit_field_value,
    handle_create_user_input
)
from modules.handlers.node_handlers import handle_nodes_menu
from modules.handlers.stats_handlers import handle_stats_menu
from modules.handlers.host_handlers import handle_hosts_menu
from modules.handlers.inbound_handlers import handle_inbounds_menu
from modules.handlers.bulk_handlers import handle_bulk_menu, handle_bulk_confirm

logger = logging.getLogger(__name__)

async def unauthorized_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unauthorized access attempts"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
    
    if update.message:
        await update.message.reply_text("⛔ Вы не авторизованы для использования этого бота.")
    elif update.callback_query:
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
    
    return ConversationHandler.END

def create_conversation_handler():
    """Create the main conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(handle_menu_selection)
            ],
            USER_MENU: [
                CallbackQueryHandler(handle_users_menu)
            ],
            NODE_MENU: [
                CallbackQueryHandler(handle_nodes_menu)
            ],
            STATS_MENU: [
                CallbackQueryHandler(handle_stats_menu)
            ],
            HOST_MENU: [
                CallbackQueryHandler(handle_hosts_menu)
            ],
            INBOUND_MENU: [
                CallbackQueryHandler(handle_inbounds_menu)
            ],
            BULK_MENU: [
                CallbackQueryHandler(handle_bulk_menu)
            ],
            SELECTING_USER: [
                CallbackQueryHandler(handle_user_selection)
            ],
            WAITING_FOR_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
            ],
            CONFIRM_ACTION: [
                CallbackQueryHandler(handle_action_confirmation)
            ],
            EDIT_USER: [
                CallbackQueryHandler(handle_edit_field_selection)
            ],
            EDIT_FIELD: [
                CallbackQueryHandler(handle_edit_field_selection)
            ],
            EDIT_VALUE: [
                CallbackQueryHandler(handle_edit_field_value),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_field_value)
            ],
            CREATE_USER: [
                CallbackQueryHandler(handle_create_user_input)
            ],
            CREATE_USER_FIELD: [
                CallbackQueryHandler(handle_create_user_input),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_user_input)
            ],
            BULK_CONFIRM: [
                CallbackQueryHandler(handle_bulk_confirm)
            ]
        },
        fallbacks=[
            CommandHandler("start", unauthorized_handler),
            MessageHandler(filters.TEXT, unauthorized_handler),
            CallbackQueryHandler(unauthorized_handler)
        ],
        name="remnawave_admin_conversation",
        persistent=False,
        per_chat=True,
        per_user=True,
        per_message=False
    )
