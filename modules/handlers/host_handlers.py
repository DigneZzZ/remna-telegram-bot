from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, HOST_MENU
from modules.api.hosts import HostAPI
from modules.utils.formatters import format_host_details
from modules.handlers.start_handler import show_main_menu

async def show_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show hosts menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех хостов", callback_data="list_hosts")],
        [InlineKeyboardButton("➕ Создать хост", callback_data="create_host")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🌐 *Управление хостами*\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hosts menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_hosts":
        await list_hosts(update, context)

    elif data == "create_host":
        # TODO: Implement create host functionality
        await query.edit_message_text(
            "🚧 Функция создания хоста находится в разработке.",
            parse_mode="Markdown"
        )
        return HOST_MENU

    elif data == "back_to_hosts":
        await show_hosts_menu(update, context)
        return HOST_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_host_"):
        uuid = data.split("_")[2]
        await show_host_details(update, context, uuid)

    elif data.startswith("enable_host_"):
        uuid = data.split("_")[2]
        await enable_host(update, context, uuid)
        return HOST_MENU

    elif data.startswith("disable_host_"):
        uuid = data.split("_")[2]
        await disable_host(update, context, uuid)
        return HOST_MENU

    elif data.startswith("edit_host_"):
        uuid = data.split("_")[2]
        # TODO: Implement edit host functionality
        await query.edit_message_text(
            "🚧 Функция редактирования хоста находится в разработке.",
            parse_mode="Markdown"
        )
        return HOST_MENU

    elif data.startswith("delete_host_"):
        uuid = data.split("_")[2]
        # TODO: Implement delete host functionality
        await query.edit_message_text(
            "🚧 Функция удаления хоста находится в разработке.",
            parse_mode="Markdown"
        )
        return HOST_MENU

    return HOST_MENU

async def list_hosts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all hosts"""
    await update.callback_query.edit_message_text("🌐 Загрузка списка хостов...")

    hosts = await HostAPI.get_all_hosts()

    if not hosts:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хосты не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return HOST_MENU

    message = f"🌐 *Хосты* ({len(hosts)}):\n\n"

    for i, host in enumerate(hosts):
        status_emoji = "🟢" if not host["isDisabled"] else "🔴"
        
        message += f"{i+1}. {status_emoji} *{host['remark']}*\n"
        message += f"   🌐 Адрес: {host['address']}:{host['port']}\n"
        message += f"   🔌 Inbound: {host['inboundUuid'][:8]}...\n\n"

    # Add action buttons
    keyboard = []
    
    for i, host in enumerate(hosts):
        keyboard.append([
            InlineKeyboardButton(f"👁️ {host['remark']}", callback_data=f"view_host_{host['uuid']}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return HOST_MENU

async def show_host_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show host details"""
    host = await HostAPI.get_host_by_uuid(uuid)
    
    if not host:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хост не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return HOST_MENU
    
    message = format_host_details(host)
    
    # Create action buttons
    keyboard = []
    
    if host["isDisabled"]:
        keyboard.append([InlineKeyboardButton("🟢 Включить", callback_data=f"enable_host_{uuid}")])
    else:
        keyboard.append([InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_host_{uuid}")])
    
    keyboard.append([InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_host_{uuid}")])
    keyboard.append([InlineKeyboardButton("❌ Удалить", callback_data=f"delete_host_{uuid}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="list_hosts")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return HOST_MENU

async def enable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Enable host"""
    await update.callback_query.answer()
    
    success = await HostAPI.enable_host(uuid)
    
    if success:
        await update.callback_query.edit_message_text("🟢 Хост успешно включен.")
    else:
        await update.callback_query.edit_message_text("❌ Не удалось включить хост.")
    
    return await show_host_details(update, context, uuid)

async def disable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable host"""
    await update.callback_query.answer()
    
    success = await HostAPI.disable_host(uuid)
    
    if success:
        await update.callback_query.edit_message_text("🔴 Хост успешно отключен.")
    else:
        await update.callback_query.edit_message_text("❌ Не удалось отключить хост.")
    
    return await show_host_details(update, context, uuid)
