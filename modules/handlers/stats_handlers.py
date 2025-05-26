from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, STATS_MENU
from modules.api.system import SystemAPI
from modules.utils.formatters import format_system_stats, format_bandwidth_stats, format_bytes
from modules.handlers.start_handler import show_main_menu

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
    await update.callback_query.edit_message_text("📊 Загрузка статистики серверов...")

    stats = await SystemAPI.get_nodes_statistics()

    if not stats or not stats.get("lastSevenDays"):
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Не удалось получить статистику серверов.",
            reply_markup=reply_markup
        )
        return STATS_MENU

    message = f"📊 *Статистика серверов за последние 7 дней*\n\n"
    
    # Group by node name
    node_stats = {}
    for entry in stats["lastSevenDays"]:
        node_name = entry.get("nodeName", "Unknown")
        if node_name not in node_stats:
            node_stats[node_name] = {
                "totalBytes": 0,
                "days": {}
            }
        
        date = entry.get("date", "Unknown")
        total_bytes = entry.get("totalBytes", "0")
        
        # Преобразуем строку в число, если возможно
        try:
            total_bytes_num = int(total_bytes)
        except (ValueError, TypeError):
            total_bytes_num = 0
        
        node_stats[node_name]["days"][date] = total_bytes
        node_stats[node_name]["totalBytes"] += total_bytes_num
    
    # Sort nodes by total traffic
    sorted_nodes = sorted(node_stats.items(), key=lambda x: x[1]["totalBytes"], reverse=True)
    
    for node_name, data in sorted_nodes:
        message += f"*{node_name}*: {format_bytes(data['totalBytes'])}\n"
        
        # Show daily breakdown
        for date, bytes_value in sorted(data["days"].items()):
            message += f"  • {date}: {bytes_value}\n"
        
        message += "\n"

    # Add back button
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return STATS_MENU
