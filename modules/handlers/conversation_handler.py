from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ConversationHandler
)
from telegram import Update
from telegram.ext import ContextTypes
import logging
import warnings

# Подавляем предупреждение PTBUserWarning о per_message=False с CallbackQueryHandler
warnings.filterwarnings("ignore", message=".*?per_message=False.*?CallbackQueryHandler", category=UserWarning)

from modules.config import (
    MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU, BULK_MENU,
    SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION,
    EDIT_USER, EDIT_FIELD, EDIT_VALUE,
    CREATE_USER, CREATE_USER_FIELD, BULK_CONFIRM, 
    EDIT_NODE, EDIT_NODE_FIELD, EDIT_HOST, EDIT_HOST_FIELD, NODE_PORT,
    CREATE_NODE, NODE_NAME, NODE_ADDRESS, SELECT_INBOUNDS,
    ADMIN_USER_IDS
)
from modules.utils.auth import check_authorization

from modules.handlers.start_handler import start
from modules.handlers.menu_handler import handle_menu_selection
from modules.handlers.user_handlers import (
    handle_users_menu, handle_user_selection, handle_user_action,
    handle_action_confirmation, handle_text_input,
    handle_edit_field_selection, handle_edit_field_value,
    handle_create_user_input
)
from modules.handlers.node_handlers import (
    handle_nodes_menu, handle_node_edit_menu, handle_node_field_input, handle_cancel_node_edit,
    handle_node_creation, show_node_certificate
)
from modules.handlers.stats_handlers import handle_stats_menu
from modules.handlers.host_handlers import (
    handle_hosts_menu, handle_host_edit_menu, handle_host_field_input, handle_cancel_host_edit
)
from modules.handlers.inbound_handlers import handle_inbounds_menu
from modules.handlers.bulk_handlers import handle_bulk_menu, handle_bulk_confirm

logger = logging.getLogger(__name__)

async def unauthorized_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unauthorized access attempts"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
        
        if update.message:
            await update.message.reply_text("⛔ Вы не авторизованы для использования этого бота.")
        elif update.callback_query:
            await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        
        return ConversationHandler.END
    
    # Если пользователь авторизован, но попал в fallback, перенаправляем на главное меню
    return await start(update, context)

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
                CallbackQueryHandler(show_node_certificate, pattern="^show_certificate_"),
                CallbackQueryHandler(show_node_certificate, pattern="^get_panel_certificate$"),
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
                CallbackQueryHandler(handle_user_action, pattern="^user_action_"),
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
            ],
            EDIT_NODE: [
                CallbackQueryHandler(handle_node_edit_menu),
                CallbackQueryHandler(handle_cancel_node_edit, pattern="^cancel_edit_node_")
            ],
            EDIT_NODE_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_field_input),
                CallbackQueryHandler(handle_cancel_node_edit, pattern="^cancel_edit_node_")
            ],
            EDIT_HOST: [
                CallbackQueryHandler(handle_host_edit_menu),
                CallbackQueryHandler(handle_cancel_host_edit, pattern="^ceh_")
            ],
            EDIT_HOST_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_host_field_input),
                CallbackQueryHandler(handle_cancel_host_edit, pattern="^ceh_")
            ],
            CREATE_NODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^cancel_create_node$"),
            ],
            NODE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^cancel_create_node$"),
            ],
            NODE_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^cancel_create_node$"),
            ],
            NODE_PORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^(cancel_create_node|use_port_3000)$"),
            ],
            SELECT_INBOUNDS: [
                CallbackQueryHandler(show_node_certificate, pattern="^show_certificate_"),
                CallbackQueryHandler(show_node_certificate, pattern="^get_panel_certificate$"),
                CallbackQueryHandler(handle_node_creation, pattern="^(select_inbound_|remove_inbound_|finish_node_creation|cancel_create_node)"),
            ],
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
