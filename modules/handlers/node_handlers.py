from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import MAIN_MENU, NODE_MENU, EDIT_NODE, EDIT_NODE_FIELD, CREATE_NODE, NODE_NAME, NODE_ADDRESS, NODE_PORT, NODE_TLS, SELECT_INBOUNDS
from modules.api.nodes import NodeAPI
from modules.api.inbounds import InboundAPI
from modules.utils.formatters import format_node_details, format_bytes
from modules.utils.selection_helpers import SelectionHelper
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def show_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show nodes menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех серверов", callback_data="list_nodes")],
        [InlineKeyboardButton("➕ Добавить новый сервер", callback_data="add_node")],
        [InlineKeyboardButton("📜 Получить сертификат панели", callback_data="get_panel_certificate")],
        [InlineKeyboardButton("🔄 Перезапустить все серверы", callback_data="restart_all_nodes")],
        [InlineKeyboardButton("📊 Статистика использования", callback_data="nodes_usage")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🖥️ *Управление серверами*\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle nodes menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_nodes":
        await list_nodes(update, context)
        return NODE_MENU
    
    elif data == "add_node":
        await start_create_node(update, context)
        return CREATE_NODE
    
    elif data == "get_panel_certificate":
        await show_node_certificate(update, context)
        return NODE_MENU

    elif data == "restart_all_nodes":
        # Confirm restart all nodes
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, перезапустить все", callback_data="confirm_restart_all"),
                InlineKeyboardButton("❌ Отмена", callback_data="back_to_nodes")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите перезапустить все серверы?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return NODE_MENU

    elif data == "confirm_restart_all":
        # Restart all nodes
        result = await NodeAPI.restart_all_nodes()
        
        if result and result.get("eventSent"):
            message = "✅ Команда на перезапуск всех серверов успешно отправлена."
        else:
            message = "❌ Ошибка при перезапуске серверов."
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return NODE_MENU
        
    elif data == "nodes_usage":
        await show_nodes_usage(update, context)
        return NODE_MENU

    elif data == "back_to_nodes":
        await show_nodes_menu(update, context)
        return NODE_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_node_"):
        uuid = data.split("_")[2]
        await show_node_details(update, context, uuid)
        return NODE_MENU
    
    elif data.startswith("select_node_"):
        # Handle SelectionHelper callback for node selection
        node_id = data.replace("select_node_", "")
        await show_node_details(update, context, node_id)
        return NODE_MENU
    
    elif data.startswith("page_nodes_"):
        # Handle pagination for node list
        page = int(data.split("_")[2])
        await handle_node_pagination(update, context, page)
        return NODE_MENU
    
    elif data.startswith("enable_node_"):
        uuid = data.split("_")[2]
        await enable_node(update, context, uuid)
        return NODE_MENU
    elif data.startswith("disable_node_"):
        uuid = data.split("_")[2]
        await disable_node(update, context, uuid)
        return NODE_MENU
    elif data.startswith("restart_node_"):
        uuid = data.split("_")[2]
        await restart_node(update, context, uuid)
        return NODE_MENU
    elif data.startswith("node_stats_"):
        uuid = data.split("_")[2]
        await show_node_stats(update, context, uuid)
        return NODE_MENU
    elif data.startswith("edit_node_"):
        uuid = data.split("_")[2]
        await start_edit_node(update, context, uuid)
        return EDIT_NODE

    return NODE_MENU

async def list_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all nodes using SelectionHelper"""
    await update.callback_query.edit_message_text("🖥️ Загрузка списка серверов...")

    try:
        # Use SelectionHelper for user-friendly display
        keyboard, nodes_data = await SelectionHelper.get_nodes_selection_keyboard(
            callback_prefix="view_node",
            include_back=True
        )
        
        # Replace back button with custom callback by creating new keyboard
        if keyboard.inline_keyboard and keyboard.inline_keyboard[-1][0].text == "🔙 Назад":
            # Create new keyboard with corrected back button
            new_keyboard = []
            for row in keyboard.inline_keyboard[:-1]:  # All rows except the last one
                new_keyboard.append(row)
            
            # Add corrected back button as last row
            new_keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")])
            keyboard = InlineKeyboardMarkup(new_keyboard)
        
        # Store nodes data in context for later use
        context.user_data["nodes_data"] = nodes_data
        
        if not nodes_data:
            await update.callback_query.edit_message_text(
                "❌ Серверы не найдены или ошибка при получении списка.",
                reply_markup=keyboard
            )
            return NODE_MENU

        # Count online/offline nodes
        online_count = sum(1 for node in nodes_data.values() 
                          if not node.get("isDisabled", False) and node.get("isConnected", False))
        total_count = len(nodes_data)
        
        message = f"🖥️ *Список серверов* ({online_count}/{total_count} онлайн)\n\n"
        message += "Выберите сервер для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка серверов.",
            reply_markup=reply_markup
        )

    return NODE_MENU

async def show_node_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show node details"""
    node = await NodeAPI.get_node_by_uuid(uuid)
    
    if not node:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Сервер не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return NODE_MENU
    
    message = format_node_details(node)
    
    # Create action buttons
    keyboard = []
    
    if node["isDisabled"]:
        keyboard.append([InlineKeyboardButton("🟢 Включить", callback_data=f"enable_node_{uuid}")])
    else:
        keyboard.append([InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_node_{uuid}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Перезапустить", callback_data=f"restart_node_{uuid}")])
    keyboard.append([InlineKeyboardButton("📊 Статистика", callback_data=f"node_stats_{uuid}")])
    keyboard.append([InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_node_{uuid}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="list_nodes")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def show_nodes_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show nodes usage statistics"""
    logger.info("Requesting nodes realtime usage statistics")
    
    # Get realtime usage
    usage = await NodeAPI.get_nodes_realtime_usage()
    
    logger.info(f"Nodes realtime usage API response: {usage}")
    
    if not usage:
        logger.warning("No usage data returned from API")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Статистика не найдена или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return NODE_MENU
    
    message = f"📊 *Статистика использования серверов*\n\n"
    
    # Sort by total bandwidth
    sorted_usage = sorted(usage, key=lambda x: x.get("totalBytes", 0), reverse=True)
    
    for i, node in enumerate(sorted_usage):
        node_name = node.get('nodeName', 'Неизвестный сервер')
        country_code = node.get('countryCode', 'N/A')
        download_bytes = node.get('downloadBytes', 0)
        upload_bytes = node.get('uploadBytes', 0)
        total_bytes = node.get('totalBytes', 0)
        download_speed = node.get('downloadSpeedBps', 0)
        upload_speed = node.get('uploadSpeedBps', 0)
        total_speed = node.get('totalSpeedBps', 0)
        
        message += f"{i+1}. *{node_name}* ({country_code})\n"
        message += f"   📥 Загрузка: {format_bytes(download_bytes)} ({format_bytes(download_speed)}/с)\n"
        message += f"   📤 Выгрузка: {format_bytes(upload_bytes)} ({format_bytes(upload_speed)}/с)\n"
        message += f"   📊 Всего: {format_bytes(total_bytes)} ({format_bytes(total_speed)}/с)\n\n"
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_usage")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def enable_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Enable node"""
    logger.info(f"Attempting to enable node with UUID: {uuid}")
    
    try:
        result = await NodeAPI.enable_node(uuid)
        logger.info(f"Enable node API result: {result}")
        
        # Проверяем различные варианты успешного ответа
        if result:
            # Если есть поле success
            if result.get("success") is True:
                message = "✅ Сервер успешно включен."
            # Если результат содержит uuid (признак успешного обновления)
            elif result.get("uuid") == uuid:
                message = "✅ Сервер успешно включен."
            # Если результат содержит isDisabled = False
            elif result.get("isDisabled") is False:
                message = "✅ Сервер успешно включен."
            else:
                message = "❌ Ошибка при включении сервера."
                logger.error(f"Unexpected API response format: {result}")
        else:
            message = "❌ Ошибка при включении сервера."
            logger.error(f"Empty or null API response: {result}")
            
    except Exception as e:
        message = "❌ Ошибка при включении сервера."
        logger.error(f"Exception while enabling node: {e}")
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def disable_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable node"""
    logger.info(f"Attempting to disable node with UUID: {uuid}")
    
    try:
        result = await NodeAPI.disable_node(uuid)
        logger.info(f"Disable node API result: {result}")
        
        # Проверяем различные варианты успешного ответа
        if result:
            # Если есть поле success
            if result.get("success") is True:
                message = "✅ Сервер успешно отключен."
            # Если результат содержит uuid (признак успешного обновления)
            elif result.get("uuid") == uuid:
                message = "✅ Сервер успешно отключен."
            # Если результат содержит isDisabled = True
            elif result.get("isDisabled") is True:
                message = "✅ Сервер успешно отключен."
            else:
                message = "❌ Ошибка при отключении сервера."
                logger.error(f"Unexpected API response format: {result}")
        else:
            message = "❌ Ошибка при отключении сервера."
            logger.error(f"Empty or null API response: {result}")
            
    except Exception as e:
        message = "❌ Ошибка при отключении сервера."
        logger.error(f"Exception while disabling node: {e}")
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def restart_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Restart node"""
    result = await NodeAPI.restart_node(uuid)
    
    if result and result.get("eventSent"):
        message = "✅ Команда на перезапуск сервера успешно отправлена."
    else:
        message = "❌ Ошибка при перезапуске сервера."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def show_node_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show node statistics"""
    await update.callback_query.edit_message_text("📊 Загрузка статистики сервера...")
    
    try:
        # Получаем информацию о узле
        node = await NodeAPI.get_node_by_uuid(uuid)
        if not node:
            keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Сервер не найден.",
                reply_markup=reply_markup
            )
            return NODE_MENU
        
        # Получаем статистику за последние 7 дней
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        usage_stats = await NodeAPI.get_node_usage_by_range(uuid, start_date, end_date)
        
        message = f"📊 *Статистика сервера {node['name']}*\n\n"
        
        # Основная информация
        status = "🟢 Включен" if not node.get("isDisabled", True) else "🔴 Отключен"
        connection = "✅ Подключен" if node.get("isConnected", False) else "❌ Не подключен"
        
        message += f"🖥️ *Статус*: {status}\n"
        message += f"🔌 *Соединение*: {connection}\n"
        message += f"🌍 *Страна*: {node.get('countryCode', 'N/A')}\n"
        message += f"📍 *Адрес*: {node.get('address', 'N/A')}\n\n"
        
        # Статистика использования
        if usage_stats and len(usage_stats) > 0:
            message += f"📈 *Статистика за последние 7 дней*:\n"
            
            total_usage = 0
            daily_stats = {}
            
            # Группируем данные по дням
            for entry in usage_stats:
                date = entry.get("date", "Unknown")
                total_bytes = entry.get("totalBytes", 0)
                
                # Преобразуем в число если это строка
                if isinstance(total_bytes, str):
                    try:
                        total_bytes = int(total_bytes)
                    except ValueError:
                        total_bytes = 0
                
                if date not in daily_stats:
                    daily_stats[date] = 0
                daily_stats[date] += total_bytes
                total_usage += total_bytes
            
            # Общее использование
            message += f"  • Общий трафик: {format_bytes(total_usage)}\n"
            message += f"  • Среднее в день: {format_bytes(total_usage / 7) if total_usage > 0 else '0 B'}\n\n"
            
            # Детальная статистика по дням (показываем последние 5 дней)
            if daily_stats:
                message += f"📅 *По дням*:\n"
                sorted_days = sorted(daily_stats.items(), reverse=True)[:5]
                for date, bytes_used in sorted_days:
                    formatted_date = date.split('T')[0] if 'T' in date else date
                    message += f"  • {formatted_date}: {format_bytes(bytes_used)}\n"
        else:
            message += f"📊 *Статистика*: Нет данных за последние 7 дней\n"
        
        # Попробуем получить realtime статистику
        try:
            realtime_usage = await NodeAPI.get_nodes_realtime_usage()
            if realtime_usage:
                # Найдем данные для нашего узла
                node_realtime = next((item for item in realtime_usage 
                                    if item.get("nodeUuid") == uuid), None)
                if node_realtime:
                    message += f"\n⚡ *Текущая активность*:\n"
                    message += f"  • Скачивание: {format_bytes(node_realtime.get('downloadSpeedBps', 0))}/с\n"
                    message += f"  • Загрузка: {format_bytes(node_realtime.get('uploadSpeedBps', 0))}/с\n"
                    message += f"  • Общая скорость: {format_bytes(node_realtime.get('totalSpeedBps', 0))}/с\n"
        except Exception as e:
            logger.warning(f"Could not get realtime stats: {e}")
        
    except Exception as e:
        logger.error(f"Error getting node statistics: {e}")
        message = "❌ Ошибка при получении статистики сервера."
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"node_stats_{uuid}")],
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def handle_node_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for node list"""
    try:
        nodes = await NodeAPI.get_all_nodes()
        
        if not nodes:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Серверы не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return NODE_MENU

        # Format items for SelectionHelper
        items = []
        for node in nodes:
            status_emoji = "🟢" if node["isConnected"] and not node["isDisabled"] else "🔴"
            
            description = f"{status_emoji} {node['address']}:{node['port']}"
            
            if node.get("usersOnline") is not None:
                description += f" | 👥 Онлайн: {node['usersOnline']}"
            
            if node.get("trafficLimitBytes") is not None:
                description += f"\n📈 Трафик: {format_bytes(node['trafficUsedBytes'])}/{format_bytes(node['trafficLimitBytes'])}"
            
            items.append({
                'id': node['uuid'],
                'name': node['name'],
                'description': description
            })

        # Use SelectionHelper for pagination
        helper = SelectionHelper(
            title="🖥️ Выберите сервер",
            items=items,
            callback_prefix="select_node",
            back_callback="back_to_nodes",
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
        logger.error(f"Error handling node pagination: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка серверов.",
            reply_markup=reply_markup
        )

    return NODE_MENU
async def start_edit_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start editing a node"""
    try:
        # Get node details
        node = await NodeAPI.get_node_by_uuid(uuid)
        if not node:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Сервер не найден.",
                reply_markup=reply_markup
            )
            return NODE_MENU
        
        # Store node data in context
        context.user_data["editing_node"] = node
        
        # Create edit menu
        keyboard = [
            [InlineKeyboardButton("📝 Имя сервера", callback_data=f"edit_node_field_name_{uuid}")],
            [InlineKeyboardButton("🌐 Адрес", callback_data=f"edit_node_field_address_{uuid}")],
            [InlineKeyboardButton("🔌 Порт", callback_data=f"edit_node_field_port_{uuid}")],
            [InlineKeyboardButton("🌍 Код страны", callback_data=f"edit_node_field_country_{uuid}")],
            [InlineKeyboardButton("📊 Множитель потребления", callback_data=f"edit_node_field_multiplier_{uuid}")],
            [InlineKeyboardButton("📈 Лимит трафика", callback_data=f"edit_node_field_traffic_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"📝 *Редактирование сервера: {node['name']}*\n\n"
        message += f"📌 Текущие значения:\n"
        message += f"• Имя: `{node['name']}`\n"
        message += f"• Адрес: `{node['address']}`\n"
        message += f"• Порт: `{node['port']}`\n"
        message += f"• Страна: `{node.get('countryCode', 'N/A')}`\n"
        message += f"• Множитель: `{node.get('consumptionMultiplier', 1)}`x\n"
        message += f"• Лимит трафика: `{format_bytes(node.get('trafficLimitBytes', 0)) if node.get('trafficLimitBytes') else 'Не установлен'}`\n\n"
        message += "Выберите поле для редактирования:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_NODE
        
    except Exception as e:
        logger.error(f"Error starting node edit: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке данных сервера.",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def handle_node_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle node edit menu selection"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("edit_node_field_"):
        parts = data.split("_")
        field = parts[3]  # name, address, port, country, multiplier, traffic
        uuid = parts[4]
        
        await start_edit_node_field(update, context, uuid, field)
        return EDIT_NODE_FIELD
    
    elif data.startswith("view_node_"):
        uuid = data.split("_")[2]
        await show_node_details(update, context, uuid)
        return NODE_MENU
    
    return EDIT_NODE

async def start_edit_node_field(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, field: str):
    """Start editing a specific node field"""
    try:
        node = context.user_data.get("editing_node")
        if not node:
            # Fallback: get node from API
            node = await NodeAPI.get_node_by_uuid(uuid)
            if not node:
                await update.callback_query.edit_message_text("❌ Ошибка: данные сервера не найдены.")
                return EDIT_NODE
            context.user_data["editing_node"] = node
        
        # Store field being edited
        context.user_data["editing_field"] = field
        
        # Get current value and field info
        field_info = {
            "name": {
                "title": "Имя сервера",
                "current": node.get("name", ""),
                "example": "Например: VPS-Server-1",
                "validation": "текст"
            },
            "address": {
                "title": "Адрес сервера",
                "current": node.get("address", ""),
                "example": "Например: 192.168.1.1 или example.com",
                "validation": "IP адрес или домен"
            },
            "port": {
                "title": "Порт сервера",
                "current": str(node.get("port", "")),
                "example": "Например: 3000",
                "validation": "число от 1 до 65535"
            },
            "country": {
                "title": "Код страны",
                "current": node.get("countryCode", ""),
                "example": "Например: US, RU, DE (2 буквы)",
                "validation": "код страны из 2 букв"
            },
            "multiplier": {
                "title": "Множитель потребления",
                "current": str(node.get("consumptionMultiplier", 1)),
                "example": "Например: 1.5 или 2",
                "validation": "число больше 0"
            },
            "traffic": {
                "title": "Лимит трафика (байты)",
                "current": str(node.get("trafficLimitBytes", 0)),
                "example": "Например: 1073741824 (1GB) или 0 (без лимита)",
                "validation": "число в байтах или 0 для снятия лимита"
            }
        }
        
        if field not in field_info:
            await update.callback_query.edit_message_text("❌ Неизвестное поле для редактирования.")
            return EDIT_NODE
        
        info = field_info[field]
        
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_node_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"📝 *Редактирование: {info['title']}*\n\n"
        message += f"📌 Текущее значение: `{info['current']}`\n\n"
        message += f"💡 {info['example']}\n"
        message += f"✅ Формат: {info['validation']}\n\n"
        message += f"✍️ Введите новое значение:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_NODE_FIELD
        
    except Exception as e:
        logger.error(f"Error starting field edit: {e}")
        await update.callback_query.edit_message_text("❌ Ошибка при подготовке редактирования.")
        return EDIT_NODE

async def handle_node_field_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input for node field editing"""
    try:
        node = context.user_data.get("editing_node")
        field = context.user_data.get("editing_field")
        
        if not node or not field:
            await update.message.reply_text("❌ Ошибка: данные редактирования потеряны.")
            return EDIT_NODE
        
        user_input = update.message.text.strip()
        uuid = node["uuid"]
        
        # Validate input based on field type
        validated_value = None
        error_message = None
        
        if field == "name":
            if len(user_input) < 1:
                error_message = "Имя не может быть пустым."
            elif len(user_input) > 100:
                error_message = "Имя слишком длинное (максимум 100 символов)."
            else:
                validated_value = user_input
        
        elif field == "address":
            if len(user_input) < 1:
                error_message = "Адрес не может быть пустым."
            else:
                validated_value = user_input
        
        elif field == "port":
            try:
                port_num = int(user_input)
                if port_num < 1 or port_num > 65535:
                    error_message = "Порт должен быть от 1 до 65535."
                else:
                    validated_value = port_num
            except ValueError:
                error_message = "Порт должен быть числом."
        
        elif field == "country":
            if len(user_input) != 2:
                error_message = "Код страны должен содержать ровно 2 буквы."
            elif not user_input.isalpha():
                error_message = "Код страны должен содержать только буквы."
            else:
                validated_value = user_input.upper()
        
        elif field == "multiplier":
            try:
                multiplier = float(user_input)
                if multiplier <= 0:
                    error_message = "Множитель должен быть больше 0."
                else:
                    validated_value = multiplier
            except ValueError:
                error_message = "Множитель должен быть числом."
        
        elif field == "traffic":
            try:
                traffic = int(user_input)
                if traffic < 0:
                    error_message = "Лимит трафика не может быть отрицательным."
                else:
                    validated_value = traffic
            except ValueError:
                error_message = "Лимит трафика должен быть числом."
        
        if error_message:
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_node_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ {error_message}\n\nПопробуйте еще раз:",
                reply_markup=reply_markup
            )
            return EDIT_NODE_FIELD
        
        # Update node via API
        update_data = {}
        
        # Map field to API field name
        api_field_map = {
            "name": "name",
            "address": "address", 
            "port": "port",
            "country": "countryCode",
            "multiplier": "consumptionMultiplier",
            "traffic": "trafficLimitBytes"
        }
        
        api_field = api_field_map.get(field)
        if not api_field:
            await update.message.reply_text("❌ Ошибка: неизвестное поле.")
            return EDIT_NODE
        
        update_data[api_field] = validated_value
        
        # Send update to API
        result = await NodeAPI.update_node(uuid, update_data)
        
        if result:
            # Update stored node data
            node[api_field] = validated_value
            context.user_data["editing_node"] = node
            
            # Clear editing state
            context.user_data.pop("editing_field", None)
            
            keyboard = [
                [InlineKeyboardButton("✅ Продолжить редактирование", callback_data=f"edit_node_{uuid}")],
                [InlineKeyboardButton("📋 Показать детали", callback_data=f"view_node_{uuid}")],
                [InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Поле '{api_field_map.get(field, field)}' успешно обновлено!",
                reply_markup=reply_markup
            )
            
            return NODE_MENU
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"edit_node_field_{field}_{uuid}")],
                [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_node_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Ошибка при обновлении сервера. Проверьте данные и попробуйте снова.",
                reply_markup=reply_markup
            )
            return EDIT_NODE_FIELD
            
    except Exception as e:
        logger.error(f"Error handling node field input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке ввода.")
        return EDIT_NODE

async def handle_cancel_node_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle canceling node edit"""
    query = update.callback_query
    await query.answer()
    
    # Clear editing state
    context.user_data.pop("editing_node", None)
    context.user_data.pop("editing_field", None)
    
    if query.data.startswith("cancel_edit_node_"):
        uuid = query.data.split("_")[-1]
        await show_node_details(update, context, uuid)
        return NODE_MENU
    else:
        await show_nodes_menu(update, context)
        return NODE_MENU
    
# =============================================================================
# NODE CREATION FUNCTIONS
# =============================================================================

async def start_create_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating a new node"""
    query = update.callback_query
    await query.answer()
    
    # Initialize node creation data
    context.user_data["create_node"] = {
        "name": "",
        "address": "",
        "port": 3000,
        "isTrafficTrackingActive": False,
        "trafficLimitBytes": 0,
        "notifyPercent": 80,
        "trafficResetDay": 1,
        "excludedInbounds": [],
        "countryCode": "XX",
        "consumptionMultiplier": 1.0
    }
    context.user_data["node_creation_step"] = "name"
    
    message = "🆕 *Создание новой ноды*\n\n"
    message += "📝 Шаг 1 из 4: Введите название для новой ноды:\n\n"
    message += "💡 Например: 'VPS-Germany-1' или 'Server-Moscow'"
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return CREATE_NODE

async def handle_node_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle node creation steps"""
    try:
        step = context.user_data.get("node_creation_step")
        node_data = context.user_data.get("create_node", {})
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            if query.data == "cancel_create_node":
                # Clear creation data
                context.user_data.pop("create_node", None)
                context.user_data.pop("node_creation_step", None)
                await show_nodes_menu(update, context)
                return NODE_MENU
            
            elif query.data == "use_port_3000":
                node_data["port"] = 3000
                context.user_data["node_creation_step"] = "inbounds"
                return await show_inbound_exclusion(update, context)
            
            elif query.data.startswith("select_inbound_"):
                inbound_id = query.data.replace("select_inbound_", "")
                if inbound_id not in node_data["excludedInbounds"]:
                    node_data["excludedInbounds"].append(inbound_id)
                return await show_inbound_exclusion(update, context)
            
            elif query.data.startswith("remove_inbound_"):
                inbound_id = query.data.replace("remove_inbound_", "")
                if inbound_id in node_data["excludedInbounds"]:
                    node_data["excludedInbounds"].remove(inbound_id)
                return await show_inbound_exclusion(update, context)
            
            elif query.data == "finish_node_creation":
                return await create_node_final(update, context)
            
            elif query.data.startswith("show_certificate_"):
                return await show_node_certificate(update, context)
        
        else:
            # Handle text input
            user_input = update.message.text.strip()
            
            if step == "name":
                if len(user_input) < 5:
                    await update.message.reply_text("❌ Название должно содержать минимум 5 символов. Попробуйте еще раз:")
                    return NODE_NAME
                
                node_data["name"] = user_input
                context.user_data["node_creation_step"] = "address"
                return await ask_for_node_address(update, context)
            
            elif step == "address":
                if len(user_input) < 2:
                    await update.message.reply_text("❌ Адрес слишком короткий. Попробуйте еще раз:")
                    return NODE_ADDRESS
                
                node_data["address"] = user_input
                context.user_data["node_creation_step"] = "port"
                return await ask_for_node_port(update, context)
            
            elif step == "port":
                try:
                    port = int(user_input)
                    if port < 1 or port > 65535:
                        await update.message.reply_text("❌ Порт должен быть от 1 до 65535. Попробуйте еще раз:")
                        return NODE_PORT
                    
                    node_data["port"] = port
                    context.user_data["node_creation_step"] = "inbounds"
                    return await show_inbound_exclusion(update, context)
                except ValueError:
                    await update.message.reply_text("❌ Порт должен быть числом. Попробуйте еще раз:")
                    return NODE_PORT
        
        # If no valid step or input, stay in current state based on step
        if step == "name":
            return CREATE_NODE
        elif step == "address":
            return NODE_ADDRESS  
        elif step == "port":
            return NODE_PORT
        else:
            return CREATE_NODE
        
    except Exception as e:
        logger.error(f"Error in node creation: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте создать ноду заново.")
        await show_nodes_menu(update, context)
        return NODE_MENU

async def ask_for_node_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for node address"""
    message = "🆕 *Создание новой ноды*\n\n"
    message += "🌐 Шаг 2 из 4: Введите адрес ноды:\n\n"
    message += "💡 Примеры:\n"
    message += "• `192.168.1.100`\n"
    message += "• `server.example.com`\n"
    message += "• `node1.vpn.com`"
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_ADDRESS

async def ask_for_node_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for node port"""
    message = "🆕 *Создание новой ноды*\n\n"
    message += "🔌 Шаг 3 из 4: Введите порт ноды:\n\n"
    message += "💡 Обычно используются:\n"
    message += "• `3000` (Remnawave Node по умолчанию)\n"
    message += "• `443` (HTTPS)\n"
    message += "• `8080` (альтернативный HTTP)\n"
    message += "• `2083` (Cloudflare compatible)"
    
    keyboard = [
        [InlineKeyboardButton("✅ Использовать 3000", callback_data="use_port_3000")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_PORT

async def show_inbound_exclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show inbound exclusion selection for the node"""
    try:
        node_data = context.user_data.get("create_node", {})
        
        # Get all available inbounds
        inbounds = await InboundAPI.get_inbounds()
        
        # Initialize excludedInbounds with all inbound IDs if not already set
        if "excludedInbounds" not in node_data or node_data["excludedInbounds"] is None:
            node_data["excludedInbounds"] = [inbound["uuid"] for inbound in inbounds]
            context.user_data["create_node"] = node_data
            
        excluded_inbounds = node_data.get("excludedInbounds", [])
        
        message = "🆕 *Создание новой ноды*\n\n"
        message += "📡 Шаг 4 из 4: Настройка inbound'ов для ноды:\n\n"
        message += "🔴 *Красный* = ОТКЛЮЧЕН (не будет работать на ноде)\n"
        message += "🟢 *Зеленый* = ВКЛЮЧЕН (будет работать на ноде)\n\n"
        
        if inbounds:
            message += "📋 *Доступные inbound'ы:*\n"
            message += "По умолчанию все inbound'ы отключены. Нажмите для изменения:\n\n"
            
            keyboard = []
            
            # Add inbound selection buttons
            for inbound in inbounds[:10]:  # Limit to 10 inbounds to avoid too many buttons
                inbound_id = inbound["uuid"]
                protocol = inbound.get("type", "Unknown")
                port = inbound.get("port", "N/A")
                tag = inbound.get("tag", "Unknown")
                
                if inbound_id in excluded_inbounds:
                    # Excluded (disabled) - red circle
                    button_text = f"🔴 {tag} ({protocol}:{port})"
                    callback_data = f"remove_inbound_{inbound_id}"
                else:
                    # Included (enabled) - green circle
                    button_text = f"🟢 {tag} ({protocol}:{port})"
                    callback_data = f"select_inbound_{inbound_id}"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        else:
            message += "ℹ️ Inbound'ы не найдены.\n\n"
            keyboard = []
        
        # Add finish button
        keyboard.append([InlineKeyboardButton("✅ Создать ноду", callback_data="finish_node_creation")])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        return SELECT_INBOUNDS
        
    except Exception as e:
        logger.error(f"Error showing inbound exclusion: {e}")
        message = "❌ Ошибка при загрузке inbound'ов."
        
        keyboard = [
            [InlineKeyboardButton("✅ Создать без настройки inbound'ов", callback_data="finish_node_creation")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup
            )
        
        return SELECT_INBOUNDS

async def create_node_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create the node with all provided data"""
    try:
        node_data = context.user_data.get("create_node", {})
        
        # Prepare data for API according to CreateNodeRequestDto
        api_data = {
            "name": node_data["name"],
            "address": node_data["address"],
            "port": node_data.get("port", 3000),
            "isTrafficTrackingActive": node_data.get("isTrafficTrackingActive", False),
            "trafficLimitBytes": node_data.get("trafficLimitBytes", 0),
            "notifyPercent": node_data.get("notifyPercent", 80),
            "trafficResetDay": node_data.get("trafficResetDay", 1),
            "excludedInbounds": node_data.get("excludedInbounds", []),
            "countryCode": node_data.get("countryCode", "XX"),
            "consumptionMultiplier": node_data.get("consumptionMultiplier", 1.0)
        }
        
        await update.callback_query.edit_message_text("⏳ Создание ноды...")
        
        # Create node via API
        result = await NodeAPI.create_node(api_data)
        
        if result and result.get("uuid"):
            node_uuid = result["uuid"]
            
            # Clear creation data
            context.user_data.pop("create_node", None)
            context.user_data.pop("node_creation_step", None)
            
            # Prepare success message
            message = "✅ *Нода успешно создана!*\n\n"
            message += f"📋 *Детали ноды:*\n"
            message += f"• Название: `{api_data['name']}`\n"
            message += f"• Адрес: `{api_data['address']}:{api_data['port']}`\n"
            message += f"• UUID: `{node_uuid}`\n"
            message += f"• Код страны: `{api_data['countryCode']}`\n"
            message += f"• Множитель потребления: `{api_data['consumptionMultiplier']}`\n\n"
            
            if api_data["excludedInbounds"]:
                message += f"❌ Исключенных inbound'ов: {len(api_data['excludedInbounds'])}\n\n"
            else:
                message += "✅ Все inbound'ы доступны на ноде\n\n"
            
            message += "🔧 *Следующие шаги:*\n"
            message += "1. Получите сертификат ноды\n"
            message += "2. Настройте ноду на сервере\n"
            message += "3. Подключите ноду к панели"
            
            # Show certificate and other options
            keyboard = [
                [InlineKeyboardButton("📜 Получить сертификат ноды", callback_data=f"show_certificate_{node_uuid}")],
                [InlineKeyboardButton("👁️ Просмотр ноды", callback_data=f"view_node_{node_uuid}")],
                [InlineKeyboardButton("🔙 К списку нод", callback_data="list_nodes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return NODE_MENU
        else:
            # Creation failed
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="add_node")],
                [InlineKeyboardButton("🔙 К меню нод", callback_data="back_to_nodes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Ошибка при создании ноды. Проверьте данные и попробуйте снова.",
                reply_markup=reply_markup
            )
            
            return NODE_MENU
            
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="add_node")],
            [InlineKeyboardButton("🔙 К меню нод", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при создании ноды: {str(e)}",
            reply_markup=reply_markup
        )
        
        return NODE_MENU

async def show_node_certificate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show node certificate for copying"""
    try:
        # Extract UUID from callback data or handle panel certificate request
        logger.info(f"show_node_certificate called with callback_data: {update.callback_query.data}")
        
        callback_data = update.callback_query.data
        node_uuid = None
        
        if callback_data == "get_panel_certificate":
            logger.info("Processing panel certificate request")
        elif callback_data.startswith("show_certificate_"):
            node_uuid = callback_data.replace("show_certificate_", "")
            logger.info(f"Extracted node_uuid: {node_uuid}")
        else:
            logger.error(f"Invalid callback_data: {callback_data}")
            await update.callback_query.edit_message_text("❌ Ошибка: неверный тип запроса.")
            return NODE_MENU
        
        await update.callback_query.edit_message_text("📜 Получение сертификата панели...")
        
        # Get public key from API using /api/keygen endpoint
        logger.info("Requesting node certificate from API...")
        certificate_data = await NodeAPI.get_node_certificate()  # This calls /api/keygen
        logger.info(f"Certificate data received: {certificate_data}")
        
        if certificate_data and certificate_data.get("pubKey"):
            pub_key = certificate_data["pubKey"]
            logger.info(f"Public key extracted successfully, length: {len(pub_key)}")
            
            # Create different keyboard based on whether we have a specific node UUID
            if node_uuid:
                keyboard = [
                    [InlineKeyboardButton("👁️ Просмотр ноды", callback_data=f"view_node_{node_uuid}")],
                    [InlineKeyboardButton("🔙 К списку нод", callback_data="list_nodes")]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("🔙 К меню нод", callback_data="back_to_nodes")]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Try to send with Markdown first, fallback to plain text if it fails
            try:
                # Prepare message with certificate
                message = "📜 *Сертификат панели для ноды*\n\n"
                message += "🔐 Используйте эту переменную для настройки ноды на сервере:\n\n"
                message += f"```\nSSL_CERT=\"{pub_key}\"\n```\n\n"
                message += "💡 *Инструкция по настройке ноды:*\n"
                message += "1. Скопируйте переменную SSL_CERT выше\n"
                message += "2. Установите Remnawave Node на ваш сервер\n"
                message += "3. Добавьте эту переменную в конфигурацию\n"
                message += "4. Настройте подключение к панели\n\n"
                message += "⚠️ *Важно:* Этот ключ нужен для безопасного подключения ноды к панели!"
                
                await update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                logger.info("Certificate sent successfully with Markdown formatting")
                
            except Exception as markdown_error:
                logger.warning(f"Markdown parsing failed, falling back to plain text: {markdown_error}")
                
                # Fallback to plain text without any formatting
                message = "📜 Сертификат панели для ноды\n\n"
                message += "🔐 Используйте эту переменную для настройки ноды на сервере:\n\n"
                message += f"SSL_CERT=\"{pub_key}\"\n\n"
                message += "💡 Инструкция по настройке ноды:\n"
                message += "1. Скопируйте переменную SSL_CERT выше\n"
                message += "2. Установите Remnawave Node на ваш сервер\n"
                message += "3. Добавьте эту переменную в конфигурацию\n"
                message += "4. Настройте подключение к панели\n\n"
                message += "⚠️ Важно: Этот ключ нужен для безопасного подключения ноды к панели!"
                
                await update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode=None
                )
                logger.info("Certificate sent successfully with plain text formatting")
            
        else:
            logger.warning(f"No pubKey found in certificate data: {certificate_data}")
            
            # Create different keyboard based on whether we have a specific node UUID
            if node_uuid:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"show_certificate_{node_uuid}")],
                    [InlineKeyboardButton("👁️ Просмотр ноды", callback_data=f"view_node_{node_uuid}")],
                    [InlineKeyboardButton("🔙 К списку нод", callback_data="list_nodes")]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data="get_panel_certificate")],
                    [InlineKeyboardButton("🔙 К меню нод", callback_data="back_to_nodes")]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Не удалось получить сертификат панели.",
                reply_markup=reply_markup
            )
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error showing node certificate: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔙 К списку нод", callback_data="list_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Ошибка при получении сертификата панели.",
            reply_markup=reply_markup
        )
        
        return NODE_MENU