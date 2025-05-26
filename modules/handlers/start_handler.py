from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from modules.config import MAIN_MENU
from modules.utils.auth import check_admin

@check_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
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

    message = "🎛️ *Главное меню Remnawave Admin*\n\n"
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
