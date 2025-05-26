import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, STATS_MENU
from modules.api.system import SystemAPI
from modules.api.nodes import NodeAPI
from modules.utils.formatters import format_system_stats, format_bandwidth_stats, format_bytes
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def show_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics menu"""
    keyboard = [
        [InlineKeyboardButton("📊 Общая статистика", callback_data="system_stats")],
        [InlineKeyboardButton("📈 Статистика трафика", callback_data="bandwidth_stats")],
        [InlineKeyboardButton("🖥️ Статистика серверов", callback_data="nodes_stats")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "📊 *Статистика системы*\n\n"
    message += "Выберите тип статистики:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle statistics menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "system_stats":
        return await show_system_stats(update, context)

    elif data == "bandwidth_stats":
        return await show_bandwidth_stats(update, context)
        
    elif data == "nodes_stats":
        return await show_nodes_stats(update, context)

    elif data == "back_to_stats":
        await show_stats_menu(update, context)
        return STATS_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU

    return STATS_MENU

async def show_system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system statistics"""
    await update.callback_query.edit_message_text("📊 Загрузка статистики системы...")

    stats = await SystemAPI.get_stats()

    if not stats:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Не удалось получить статистику системы.",
            reply_markup=reply_markup
        )
        return STATS_MENU

    try:
        message = format_system_stats(stats)
    except Exception as e:
        # Логируем ошибку и показываем сообщение об ошибке
        import logging
        logging.error(f"Error formatting system stats: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при форматировании статистики: {str(e)}",
            reply_markup=reply_markup
        )
        return STATS_MENU

    # Add back button
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="system_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return STATS_MENU

async def show_bandwidth_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bandwidth statistics"""
    await update.callback_query.edit_message_text("📈 Загрузка статистики трафика...")

    stats = await SystemAPI.get_bandwidth_stats()

    if not stats:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Не удалось получить статистику трафика.",
            reply_markup=reply_markup
        )
        return STATS_MENU

    message = format_bandwidth_stats(stats)

    # Add back button
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="bandwidth_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return STATS_MENU

async def show_nodes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show nodes statistics"""
    query = update.callback_query
    await query.answer()
    
    try:
        logger.info("Starting nodes stats request")
        await query.edit_message_text("📊 Загрузка статистики серверов...")
        
        # Get nodes stats from API
        logger.info("Calling NodeAPI.get_nodes_stats()")
        nodes_stats = await NodeAPI.get_nodes_stats()
        logger.info(f"NodeAPI.get_nodes_stats() returned: {nodes_stats}")
        
        if not nodes_stats:
            logger.warning("nodes_stats is None or empty")
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ Не удалось получить статистику серверов.",
                reply_markup=reply_markup
            )
            return STATS_MENU
        
        # Format nodes statistics
        message = "🖥️ *Статистика серверов*\n\n"
        
        total_nodes = len(nodes_stats)
        online_nodes = sum(1 for node in nodes_stats if node.get('status') == 'connected')
        
        message += f"📊 *Общая информация:*\n"
        message += f"• Всего серверов: {total_nodes}\n"
        message += f"• Онлайн: {online_nodes}\n"
        message += f"• Офлайн: {total_nodes - online_nodes}\n\n"
        
        if nodes_stats:
            message += "📋 *Детали серверов:*\n"
            for node in nodes_stats:
                name = node.get('name', 'Неизвестно')
                status = '🟢' if node.get('status') == 'connected' else '🔴'
                uptime = node.get('uptime', 'N/A')
                message += f"• {status} {name} (Uptime: {uptime})\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return STATS_MENU
        
    except Exception as e:
        logger.error(f"Error in show_nodes_stats: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Не удалось получить статистику серверов.",
            reply_markup=reply_markup
        )
        return STATS_MENU
