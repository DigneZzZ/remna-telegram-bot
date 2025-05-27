from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import MAIN_MENU, INBOUND_MENU
from modules.api.inbounds import InboundAPI
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.utils.formatters import format_inbound_details
from modules.utils.selection_helpers import SelectionHelper
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

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

    elif data.startswith("select_inbound_"):
        # Handle SelectionHelper callback for inbound selection
        inbound_id = data.replace("select_inbound_", "")
        await show_inbound_details(update, context, inbound_id)

    elif data.startswith("select_full_inbound_"):
        # Handle SelectionHelper callback for full inbound selection
        inbound_id = data.replace("select_full_inbound_", "")
        await show_inbound_details(update, context, inbound_id)

    elif data.startswith("page_inbounds_"):
        # Handle pagination for inbound list
        page = int(data.split("_")[2])
        await handle_inbound_pagination(update, context, page)

    elif data.startswith("page_full_inbounds_"):
        # Handle pagination for full inbound list
        page = int(data.split("_")[3])
        await handle_full_inbound_pagination(update, context, page)

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
    """List all inbounds using SelectionHelper"""
    await update.callback_query.edit_message_text("🔌 Загрузка списка Inbounds...")

    try:
        # Use SelectionHelper for user-friendly display
        keyboard, inbounds_data = await SelectionHelper.get_inbounds_selection_keyboard(
            callback_prefix="select_inbound",
            include_back=True
        )
        
        # Replace back button with custom callback by creating new keyboard
        if keyboard.inline_keyboard and keyboard.inline_keyboard[-1][0].text == "🔙 Назад":
            # Create new keyboard with corrected back button
            new_keyboard = []
            for row in keyboard.inline_keyboard[:-1]:  # All rows except the last one
                new_keyboard.append(row)
            
            # Add corrected back button as last row
            new_keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")])
            keyboard = InlineKeyboardMarkup(new_keyboard)
        
        if not inbounds_data:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        message = f"🔌 *Список Inbounds* ({len(inbounds_data)} шт.)\n\n"
        message += "Выберите Inbound для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error listing inbounds: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def list_full_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all inbounds with full details using SelectionHelper"""
    await update.callback_query.edit_message_text("🔌 Загрузка полного списка Inbounds...")

    try:
        inbounds = await InboundAPI.get_full_inbounds()

        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Format items for SelectionHelper with detailed info
        items = []
        for inbound in inbounds:
            description = f"🔌 {inbound['type']} | 🔢 Порт: {inbound['port']}"
            
            if 'users' in inbound:
                description += f"\n👥 Пользователи: {inbound['users']['enabled']} активных, {inbound['users']['disabled']} отключенных"
            
            if 'nodes' in inbound:
                description += f"\n🖥️ Серверы: {inbound['nodes']['enabled']} активных, {inbound['nodes']['disabled']} отключенных"
            
            items.append({
                'id': inbound['uuid'],
                'name': inbound['tag'],
                'description': description
            })

        # Use SelectionHelper for user-friendly display with detailed info
        keyboard = []
        inbounds_data = {}
        
        for inbound in inbounds:
            display_name = f"🔌 {inbound['tag']} ({inbound['type']}, :{inbound['port']})"
            callback_data = f"select_full_inbound_{inbound['uuid']}"
            inbounds_data[inbound['uuid']] = inbound
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f"🔌 *Список Inbounds с подробностями* ({len(inbounds)} шт.)\n\n"
        message += "Выберите Inbound для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error listing full inbounds: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=reply_markup
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
        result = await InboundAPI.add_inbound_to_users(uuid)
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
        result = await InboundAPI.remove_inbound_from_users(uuid)
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
        result = await InboundAPI.add_inbound_to_nodes(uuid)
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
        result = await InboundAPI.remove_inbound_from_nodes(uuid)
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

async def handle_inbound_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for inbound list"""
    try:
        inbounds = await InboundAPI.get_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Format items for SelectionHelper
        items = []
        for inbound in inbounds:
            items.append({
                'id': inbound['uuid'],
                'name': inbound['tag'],
                'description': f"🔌 {inbound['type']} | 🔢 Порт: {inbound['port']}"
            })

        # Use SelectionHelper for pagination
        helper = SelectionHelper(
            title="🔌 Выберите Inbound",
            items=items,
            callback_prefix="select_inbound",
            back_callback="back_to_inbounds",
            items_per_page=8
        )

        keyboard = helper.get_keyboard(page=page)
        message = helper.get_message(page=page)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error handling inbound pagination: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def handle_full_inbound_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for full inbound list"""
    try:
        inbounds = await InboundAPI.get_full_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Format items for SelectionHelper with detailed info
        items = []
        for inbound in inbounds:
            description = f"🔌 {inbound['type']} | 🔢 Порт: {inbound['port']}"
            
            if 'users' in inbound:
                description += f"\n👥 Пользователи: {inbound['users']['enabled']} активных, {inbound['users']['disabled']} отключенных"
            
            if 'nodes' in inbound:
                description += f"\n🖥️ Серверы: {inbound['nodes']['enabled']} активных, {inbound['nodes']['disabled']} отключенных"
            
            items.append({
                'id': inbound['uuid'],
                'name': inbound['tag'],
                'description': description
            })

        # Use SelectionHelper for pagination
        helper = SelectionHelper(
            title="🔌 Выберите Inbound (детальный просмотр)",
            items=items,
            callback_prefix="select_full_inbound",
            back_callback="back_to_inbounds",
            items_per_page=6
        )

        keyboard = helper.get_keyboard(page=page)
        message = helper.get_message(page=page)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error handling full inbound pagination: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=reply_markup
        )

    return INBOUND_MENU
