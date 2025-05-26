from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, INBOUND_MENU
from modules.api.inbounds import InboundAPI
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.utils.formatters import format_inbound_details
from modules.handlers.start_handler import show_main_menu

async def show_inbounds_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show inbounds menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех Inbounds", callback_data="list_inbounds")],
        [InlineKeyboardButton("📋 Список с деталями", callback_data="list_full_inbounds")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🔌 *Управление Inbounds*\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_inbounds_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inbounds menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_inbounds":
        await list_inbounds(update, context)

    elif data == "list_full_inbounds":
        await list_full_inbounds(update, context)

    elif data == "back_to_inbounds":
        await show_inbounds_menu(update, context)
        return INBOUND_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_inbound_"):
        uuid = data.split("_")[2]
        await show_inbound_details(update, context, uuid)

    elif data.startswith("add_to_users_"):
        uuid = data.split("_")[3]
        await add_inbound_to_all_users(update, context, uuid)
        return INBOUND_MENU

    elif data.startswith("remove_from_users_"):
        uuid = data.split("_")[3]
        await remove_inbound_from_all_users(update, context, uuid)
        return INBOUND_MENU

    elif data.startswith("add_to_nodes_"):
        uuid = data.split("_")[3]
        await add_inbound_to_all_nodes(update, context, uuid)
        return INBOUND_MENU

    elif data.startswith("remove_from_nodes_"):
        uuid = data.split("_")[3]
        await remove_inbound_from_all_nodes(update, context, uuid)
        return INBOUND_MENU

    return INBOUND_MENU

async def list_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all inbounds"""
    await update.callback_query.edit_message_text("🔌 Загрузка списка Inbounds...")

    inbounds = await InboundAPI.get_inbounds()

    if not inbounds:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Inbounds не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return INBOUND_MENU

    message = f"🔌 *Inbounds* ({len(inbounds)}):\n\n"

    for i, inbound in enumerate(inbounds):
        message += f"{i+1}. *{inbound['tag']}*\n"
        message += f"   🆔 UUID: `{inbound['uuid']}`\n"
        message += f"   🔌 Тип: {inbound['type']}\n"
        message += f"   🔢 Порт: {inbound['port']}\n\n"

    # Add action buttons
    keyboard = []
    
    for i, inbound in enumerate(inbounds):
        keyboard.append([
            InlineKeyboardButton(f"👁️ {inbound['tag']}", callback_data=f"view_inbound_{inbound['uuid']}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return INBOUND_MENU

async def list_full_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all inbounds with full details"""
    await update.callback_query.edit_message_text("🔌 Загрузка полного списка Inbounds...")

    inbounds = await InboundAPI.get_full_inbounds()

    if not inbounds:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Inbounds не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return INBOUND_MENU

    message = f"🔌 *Inbounds с деталями* ({len(inbounds)}):\n\n"

    for i, inbound in enumerate(inbounds):
        message += f"{i+1}. *{inbound['tag']}*\n"
        message += f"   🆔 UUID: `{inbound['uuid']}`\n"
        message += f"   🔌 Тип: {inbound['type']}\n"
        message += f"   🔢 Порт: {inbound['port']}\n"
        
        if 'users' in inbound:
            message += f"   👥 Пользователи: {inbound['users']['enabled']} активных, {inbound['users']['disabled']} отключенных\n"
        
        if 'nodes' in inbound:
            message += f"   🖥️ Серверы: {inbound['nodes']['enabled']} активных, {inbound['nodes']['disabled']} отключенных\n"
        
        message += "\n"

    # Add action buttons
    keyboard = []
    
    for i, inbound in enumerate(inbounds):
        keyboard.append([
            InlineKeyboardButton(f"👁️ {inbound['tag']}", callback_data=f"view_inbound_{inbound['uuid']}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return INBOUND_MENU

async def show_inbound_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show inbound details"""
    # Get full inbounds to find the one with matching UUID
    inbounds = await InboundAPI.get_full_inbounds()
    
    if not inbounds:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Inbound не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return INBOUND_MENU
    
    inbound = next((i for i in inbounds if i['uuid'] == uuid), None)
    
    if not inbound:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Inbound не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return INBOUND_MENU
    
    message = format_inbound_details(inbound)
    
    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить всем пользователям", callback_data=f"add_to_users_{uuid}"),
            InlineKeyboardButton("➖ Удалить у всех пользователей", callback_data=f"remove_from_users_{uuid}")
        ],
        [
            InlineKeyboardButton("➕ Добавить всем серверам", callback_data=f"add_to_nodes_{uuid}"),
            InlineKeyboardButton("➖ Удалить у всех серверов", callback_data=f"remove_from_nodes_{uuid}")
        ],
        [InlineKeyboardButton("🔙 Назад к списку", callback_data="list_full_inbounds")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return INBOUND_MENU

async def add_inbound_to_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Add inbound to all users"""
    await update.callback_query.answer("➕ Добавляю Inbound всем пользователям...")
    
    try:
        result = await UserAPI.add_inbound_to_all_users(uuid)
        await update.callback_query.edit_message_text(f"✅ Inbound успешно добавлен всем пользователям. Затронуто пользователей: {result}")
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ Ошибка при добавлении Inbound всем пользователям: {e}")

    keyboard = [[InlineKeyboardButton("🔙 Назад к списку", callback_data="list_full_inbounds")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=update.callback_query.message.text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return INBOUND_MENU

async def remove_inbound_from_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Remove inbound from all users"""
    await update.callback_query.answer("➖ Удаляю Inbound у всех пользователей...")
    
    try:
        result = await UserAPI.remove_inbound_from_all_users(uuid)
        await update.callback_query.edit_message_text(f"✅ Inbound успешно удален у всех пользователей. Затронуто пользователей: {result}")
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ Ошибка при удалении Inbound у всех пользователей: {e}")

    keyboard = [[InlineKeyboardButton("🔙 Назад к списку", callback_data="list_full_inbounds")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=update.callback_query.message.text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return INBOUND_MENU

async def add_inbound_to_all_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Add inbound to all nodes"""
    await update.callback_query.answer("➕ Добавляю Inbound всем серверам...")
    
    try:
        result = await NodeAPI.add_inbound_to_all_nodes(uuid)
        await update.callback_query.edit_message_text(f"✅ Inbound успешно добавлен всем серверам. Затронуто серверов: {result}")
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ Ошибка при добавлении Inbound всем серверам: {e}")

    keyboard = [[InlineKeyboardButton("🔙 Назад к списку", callback_data="list_full_inbounds")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=update.callback_query.message.text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return INBOUND_MENU

async def remove_inbound_from_all_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Remove inbound from all nodes"""
    await update.callback_query.answer("➖ Удаляю Inbound у всех серверов...")
    
    try:
        result = await NodeAPI.remove_inbound_from_all_nodes(uuid)
        await update.callback_query.edit_message_text(f"✅ Inbound успешно удален у всех серверов. Затронуто серверов: {result}")
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ Ошибка при удалении Inbound у всех серверов: {e}")

    keyboard = [[InlineKeyboardButton("🔙 Назад к списку", callback_data="list_full_inbounds")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=update.callback_query.message.text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return INBOUND_MENU
