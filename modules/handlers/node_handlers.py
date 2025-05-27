from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import logging
import re

from modules.handlers.auth import AuthFilter
from modules.handlers.states import NodeStates
from modules.api.client import RemnaAPI
from modules.api.nodes import get_all_nodes, get_node_by_uuid
from modules.api.users import get_all_users
from modules.api.system import SystemAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown
)

logger = logging.getLogger(__name__)

router = Router()

# ================ UTILITY FUNCTIONS ================

def format_node_details(node: dict) -> str:
    """Format node details for display"""
    try:
        name = escape_markdown(node.get('name', 'Unknown'))
        uuid = node.get('uuid', 'N/A')
        address = escape_markdown(node.get('address', 'Unknown'))
        port = node.get('port', 'N/A')
        
        # Status information
        is_connected = node.get('isConnected', False)
        is_disabled = node.get('isDisabled', False)
        
        status_emoji = "🟢" if is_connected else "🔴"
        connection_status = "Подключен" if is_connected else "Не подключен"
        
        disabled_status = ""
        if is_disabled:
            disabled_status = " (⏸️ Отключен)"
        
        # Build details text
        details = f"🖥️ **Сервер: {name}**{disabled_status}\n\n"
        details += f"**📊 Основная информация:**\n"
        details += f"• Статус: {status_emoji} {connection_status}\n"
        details += f"• UUID: `{uuid}`\n"
        details += f"• Адрес: `{address}:{port}`\n"
        
        # Country information
        if node.get('countryCode'):
            details += f"• Страна: {node.get('countryCode')}\n"
        
        # Traffic information
        if node.get('isTrafficTrackingActive'):
            details += f"\n**📈 Трафик:**\n"
            details += f"• Отслеживание: ✅ Включено\n"
            
            if node.get('trafficLimitBytes'):
                limit = node.get('trafficLimitBytes')
                used = node.get('trafficUsedBytes', 0)
                details += f"• Лимит: {format_bytes(limit)}\n"
                details += f"• Использовано: {format_bytes(used)}\n"
                
                if limit > 0:
                    percentage = (used / limit) * 100
                    details += f"• Использовано: {percentage:.1f}%\n"
            else:
                details += f"• Лимит: Безлимитный\n"
        else:
            details += f"\n**📈 Трафик:** Отслеживание отключено\n"
        
        # Version and timing information
        details += f"\n**🔧 Техническая информация:**\n"
        
        if node.get('version'):
            details += f"• Версия: {escape_markdown(node.get('version'))}\n"
        
        if node.get('createdAt'):
            details += f"• Создан: {format_datetime(node.get('createdAt'))}\n"
        
        if node.get('lastSeen'):
            details += f"• Последняя связь: {format_datetime(node.get('lastSeen'))}\n"
        
        if node.get('uptime'):
            uptime_str = format_uptime(node.get('uptime'))
            details += f"• Время работы: {uptime_str}\n"
        
        return details
        
    except Exception as e:
        logger.error(f"Error formatting node details: {e}")
        return f"❌ Ошибка форматирования данных сервера: {e}"

def format_uptime(uptime_seconds: int) -> str:
    """Format uptime in human readable format"""
    try:
        if isinstance(uptime_seconds, str):
            uptime_seconds = int(uptime_seconds)
            
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    except Exception:
        return str(uptime_seconds)

# ================ MAIN NODES MENU ================

@router.callback_query(F.data == "nodes", AuthFilter())
async def handle_nodes_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle nodes menu selection"""
    await state.clear()
    await show_nodes_menu(callback)

async def show_nodes_menu(callback: types.CallbackQuery):
    """Show nodes menu"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Список всех серверов", callback_data="list_nodes"))
    builder.row(types.InlineKeyboardButton(text="➕ Добавить новый сервер", callback_data="add_node"))
    builder.row(types.InlineKeyboardButton(text="📜 Получить сертификат панели", callback_data="get_panel_certificate"))
    builder.row(
        types.InlineKeyboardButton(text="🔄 Перезапустить все", callback_data="restart_all_nodes"),
        types.InlineKeyboardButton(text="📊 Статистика", callback_data="nodes_usage")
    )
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "🖥️ **Управление серверами**\n\n"
    try:
        # Получаем быструю статистику для превью через HTTP API
        nodes_list = await get_all_nodes()
        
        if nodes_list:
            total_nodes = len(nodes_list)
            online_nodes = sum(1 for node in nodes_list if node.get('isConnected', False))
            offline_nodes = total_nodes - online_nodes
            
            message += f"**📊 Статистика серверов:**\n"
            message += f"• Всего: {total_nodes}\n"
            message += f"• Онлайн: {online_nodes}\n"
            message += f"• Офлайн: {offline_nodes}\n\n"
        else:
            message += "**📊 Статистика:** Серверы не найдены\n\n"
    except Exception as e:
        logger.error(f"Error getting nodes stats: {e}")
        message += "**📊 Статистика:** Недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.answer()
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ LIST NODES ================

@router.callback_query(F.data == "list_nodes", AuthFilter())
async def list_nodes(callback: types.CallbackQuery, state: FSMContext):
    """List all nodes"""
    await callback.answer()
    await callback.message.edit_text("🖥️ Загрузка списка серверов...")
    
    try:
        # Получаем все ноды через HTTP API
        nodes_list = await get_all_nodes()
        
        if not nodes_list:
            await callback.message.edit_text(
                "❌ Серверы не найдены или ошибка при получении списка.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
                ]])
            )
            return
        
        # Store nodes data in state
        await state.update_data(nodes=nodes_list, page=0)
        await state.set_state(NodeStates.selecting_node)
        
        # Count online/offline nodes
        online_count = sum(1 for node in nodes_list if node.get('isConnected', False))
        total_count = len(nodes_list)
        
        message = f"🖥️ **Список серверов** ({online_count}/{total_count} онлайн)\n\n"
        
        # Show first 8 nodes
        builder = InlineKeyboardBuilder()
        for i, node in enumerate(nodes_list[:8]):
            status_emoji = "🟢" if node.get('isConnected', False) else "🔴"
            disabled_emoji = "⏸️" if node.get('isDisabled', False) else ""
            
            node_name = node.get('name', f"Node {node.get('uuid', 'Unknown')[:8]}")
            button_text = f"{status_emoji}{disabled_emoji} {node_name}"
            builder.row(types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_node:{node.get('uuid')}"
            ))
        
        # Pagination if needed
        if len(nodes_list) > 8:
            builder.row(
                types.InlineKeyboardButton(text="◀️", callback_data="nodes_page:0"),
                types.InlineKeyboardButton(text="▶️", callback_data="nodes_page:1")
            )
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes"))
        
        message += "Выберите сервер для просмотра подробной информации:"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке списка серверов.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
            ]])
        )

# ================ NODE PAGINATION ================

@router.callback_query(F.data.startswith("nodes_page:"), AuthFilter())
async def handle_node_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle node list pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    nodes_list = data.get('nodes', [])
    
    if not nodes_list:
        await callback.answer("❌ Данные серверов не найдены", show_alert=True)
        return
    
    items_per_page = 8
    total_pages = (len(nodes_list) + items_per_page - 1) // items_per_page
    
    if page < 0 or page >= total_pages:
        await callback.answer("❌ Неверная страница", show_alert=True)
        return
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_nodes = nodes_list[start_idx:end_idx]
    
    online_count = sum(1 for node in nodes_list if node.get('isConnected', False))
    total_count = len(nodes_list)
    
    message = f"🖥️ **Список серверов** ({online_count}/{total_count} онлайн)\n"
    message += f"Страница {page + 1} из {total_pages}\n\n"
    
    builder = InlineKeyboardBuilder()
    for node in page_nodes:
        status_emoji = "🟢" if node.get('isConnected', False) else "🔴"
        disabled_emoji = "⏸️" if node.get('isDisabled', False) else ""
        
        node_name = node.get('name', f"Node {node.get('uuid', 'Unknown')[:8]}")
        button_text = f"{status_emoji}{disabled_emoji} {node_name}"
        builder.row(types.InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_node:{node.get('uuid')}"
        ))
    
    # Pagination controls
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="◀️", callback_data=f"nodes_page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(text="▶️", callback_data=f"nodes_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes"))
    
    message += "Выберите сервер для просмотра подробной информации:"
    
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ VIEW NODE DETAILS ================

@router.callback_query(F.data.startswith("view_node:"), AuthFilter())
async def show_node_details(callback: types.CallbackQuery, state: FSMContext):
    """Show node details"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Получаем ноду через HTTP API
        node = await get_node_by_uuid(node_uuid)
        
        if not node:
            await callback.message.edit_text(
                "❌ Сервер не найден или ошибка при получении данных.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_nodes")
                ]])
            )
            return
        
        # Store current node in state
        await state.update_data(current_node=node)
        await state.set_state(NodeStates.viewing_node)
        
        # Format node details
        message = format_node_details(node)
        
        # Create action buttons
        builder = InlineKeyboardBuilder()
        
        # Status control
        if node.get('isDisabled', False):
            builder.row(types.InlineKeyboardButton(text="🟢 Включить", callback_data=f"enable_node:{node_uuid}"))
        else:
            builder.row(types.InlineKeyboardButton(text="🔴 Отключить", callback_data=f"disable_node:{node_uuid}"))
        
        # Actions
        builder.row(
            types.InlineKeyboardButton(text="🔄 Перезапустить", callback_data=f"restart_node:{node_uuid}"),
            types.InlineKeyboardButton(text="📊 Статистика", callback_data=f"node_stats:{node_uuid}")
        )
        builder.row(
            types.InlineKeyboardButton(text="📝 Редактировать", callback_data=f"edit_node:{node_uuid}"),
            types.InlineKeyboardButton(text="📜 Сертификат", callback_data=f"show_certificate:{node_uuid}")
        )
        builder.row(
            types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_node:{node_uuid}"),
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_node:{node_uuid}")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="list_nodes"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing node details: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении данных сервера",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_nodes")
            ]])
        )

# ================ NODE ACTIONS ================

@router.callback_query(F.data.startswith("enable_node:"), AuthFilter())
async def enable_node(callback: types.CallbackQuery, state: FSMContext):
    """Enable node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Включаем ноду через HTTP API
        response = await RemnaAPI.patch(f"nodes/{node_uuid}", data={"isDisabled": False})
        
        if response:
            await callback.answer("✅ Сервер включен", show_alert=True)
            # Refresh node details
            await show_node_details(callback, state)
        else:
            await callback.answer("❌ Ошибка при включении сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error enabling node: {e}")
        await callback.answer("❌ Ошибка при включении сервера", show_alert=True)

@router.callback_query(F.data.startswith("disable_node:"), AuthFilter())
async def disable_node(callback: types.CallbackQuery, state: FSMContext):
    """Disable node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Отключаем ноду через HTTP API
        response = await RemnaAPI.patch(f"nodes/{node_uuid}", data={"isDisabled": True})
        
        if response:
            await callback.answer("✅ Сервер отключен", show_alert=True)
            # Refresh node details
            await show_node_details(callback, state)
        else:
            await callback.answer("❌ Ошибка при отключении сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error disabling node: {e}")
        await callback.answer("❌ Ошибка при отключении сервера", show_alert=True)

@router.callback_query(F.data.startswith("restart_node:"), AuthFilter())
async def restart_node(callback: types.CallbackQuery, state: FSMContext):
    """Restart node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Перезапускаем ноду через HTTP API
        response = await RemnaAPI.post(f"nodes/{node_uuid}/restart")
        
        if response:
            await callback.answer("✅ Команда на перезапуск отправлена", show_alert=True)
        else:
            await callback.answer("❌ Ошибка при перезапуске сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error restarting node: {e}")
        await callback.answer("❌ Ошибка при перезапуске сервера", show_alert=True)

@router.callback_query(F.data.startswith("refresh_node:"), AuthFilter())
async def refresh_node(callback: types.CallbackQuery, state: FSMContext):
    """Refresh node details"""
    await callback.answer("🔄 Обновление данных...")
    await show_node_details(callback, state)

@router.callback_query(F.data.startswith("delete_node:"), AuthFilter())
async def delete_node_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm node deletion"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    data = await state.get_data()
    current_node = data.get('current_node', {})
    node_name = current_node.get('name', 'Unknown')
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🗑️ Да, удалить",
        callback_data=f"confirm_delete_node:{node_uuid}"
    ))
    builder.row(types.InlineKeyboardButton(
        text="❌ Отмена",
        callback_data=f"view_node:{node_uuid}"
    ))
    
    await callback.message.edit_text(
        f"🗑️ **Удаление сервера**\n\n"
        f"**Сервер:** {escape_markdown(node_name)}\n"
        f"**UUID:** `{node_uuid}`\n\n"
        f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        f"Все данные сервера будут удалены.\n\n"
        f"Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("confirm_delete_node:"), AuthFilter())
async def confirm_delete_node(callback: types.CallbackQuery, state: FSMContext):
    """Confirm node deletion"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Удаляем ноду через HTTP API
        response = await RemnaAPI.delete(f"nodes/{node_uuid}")
        
        if response:
            await callback.answer("✅ Сервер удален", show_alert=True)
            await state.clear()
            await callback.message.edit_text(
                "✅ **Сервер успешно удален**",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="📋 К списку серверов", callback_data="list_nodes"),
                    types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при удалении сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error deleting node: {e}")
        await callback.answer("❌ Ошибка при удалении сервера", show_alert=True)

# ================ NODE STATISTICS ================

@router.callback_query(F.data.startswith("node_stats:"), AuthFilter())
async def show_node_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show node statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики сервера...")
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Получаем информацию о ноде через HTTP API
        node = await get_node_by_uuid(node_uuid)
        if not node:
            await callback.message.edit_text(
                "❌ Сервер не найден.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_node:{node_uuid}")
                ]])
            )
            return
        
        node_name = escape_markdown(node.get('name', 'Unknown'))
        message = f"📊 **Статистика сервера {node_name}**\n\n"
        
        # Основная информация
        is_disabled = node.get('isDisabled', False)
        is_connected = node.get('isConnected', False)
        
        status = "🟢 Включен" if not is_disabled else "🔴 Отключен"
        connection = "✅ Подключен" if is_connected else "❌ Не подключен"
        
        message += f"🖥️ **Статус:** {status}\n"
        message += f"🔌 **Соединение:** {connection}\n"
        message += f"🌍 **Страна:** {node.get('countryCode', 'N/A')}\n"
        message += f"📍 **Адрес:** {node.get('address')}:{node.get('port')}\n\n"
        
        # Статистика пользователей на ноде
        try:
            users_list = await get_all_users()
            if users_list:
                # Фильтруем пользователей по ноде (если есть привязка)
                node_users = [user for user in users_list if user.get('nodeUuid') == node_uuid]
                
                if not node_users:
                    # Если нет прямой привязки, распределяем пользователей равномерно между нодами
                    nodes_list = await get_all_nodes()
                    if nodes_list and len(nodes_list) > 0:
                        users_per_node = len(users_list) // len(nodes_list)
                        node_index = next((i for i, n in enumerate(nodes_list) if n.get('uuid') == node_uuid), 0)
                        start_idx = node_index * users_per_node
                        end_idx = start_idx + users_per_node
                        node_users = users_list[start_idx:end_idx] if start_idx < len(users_list) else []
                
                active_users = sum(1 for user in node_users if user.get('status') == 'ACTIVE')
                total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in node_users)
                
                message += f"👥 **Пользователи на ноде:**\n"
                message += f"  • Всего: {len(node_users)}\n"
                message += f"  • Активных: {active_users}\n"
                message += f"  • Общий трафик: {format_bytes(total_traffic)}\n\n"
        except Exception as e:
            logger.warning(f"Could not get users stats for node: {e}")
        
        # Статистика трафика ноды
        if node.get('isTrafficTrackingActive'):
            used = node.get('trafficUsedBytes', 0)
            limit = node.get('trafficLimitBytes', 0)
            
            message += f"📈 **Трафик ноды:**\n"
            message += f"  • Использовано: {format_bytes(used)}\n"
            if limit > 0:
                message += f"  • Лимит: {format_bytes(limit)}\n"
                usage_percent = (used / limit) * 100 if limit > 0 else 0
                message += f"  • Использовано: {usage_percent:.1f}%\n"
            else:
                message += f"  • Лимит: Безлимитный\n"
            message += "\n"
        
        # Дополнительная информация
        if node.get('lastSeen'):
            message += f"🕐 **Последняя активность:** {format_datetime(node.get('lastSeen'))}\n"
        
        if node.get('version'):
            message += f"🔧 **Версия:** {escape_markdown(node.get('version'))}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"node_stats:{node_uuid}"),
            types.InlineKeyboardButton(text="📈 Детальная", callback_data=f"node_stats_detailed:{node_uuid}")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к серверу", callback_data=f"view_node:{node_uuid}"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting node statistics: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики сервера.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_node:{node_uuid}")
            ]])
        )

# ================ NODES USAGE STATISTICS ================

@router.callback_query(F.data == "nodes_usage", AuthFilter())
async def show_nodes_usage(callback: types.CallbackQuery, state: FSMContext):
    """Show nodes usage statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики использования серверов...")
    
    try:
        # Получаем все ноды через HTTP API
        nodes_list = await get_all_nodes()
        if not nodes_list:
            await callback.message.edit_text(
                "❌ Серверы не найдены.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
                ]])
            )
            return
        
        # Получаем статистику пользователей для подсчета трафика
        users_list = await get_all_users()
        users_by_node = {}
        
        if users_list:
            # Распределяем пользователей по нодам
            for i, user in enumerate(users_list):
                # Если есть прямая привязка к ноде
                node_uuid = user.get('nodeUuid')
                if node_uuid and any(n.get('uuid') == node_uuid for n in nodes_list):
                    if node_uuid not in users_by_node:
                        users_by_node[node_uuid] = []
                    users_by_node[node_uuid].append(user)
                else:
                    # Равномерно распределяем пользователей между нодами
                    node_index = i % len(nodes_list)
                    node_uuid = nodes_list[node_index].get('uuid')
                    if node_uuid not in users_by_node:
                        users_by_node[node_uuid] = []
                    users_by_node[node_uuid].append(user)
        
        message = f"📊 **Статистика использования серверов**\n\n"
        
        # Сортируем ноды по трафику
        node_stats = []
        for node in nodes_list:
            node_uuid = node.get('uuid')
            node_users = users_by_node.get(node_uuid, [])
            total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in node_users)
            active_users = sum(1 for user in node_users if user.get('status') == 'ACTIVE')
            
            node_stats.append({
                'node': node,
                'users': node_users,
                'active_users': active_users,
                'total_traffic': total_traffic
            })
        
        # Сортируем по трафику
        node_stats.sort(key=lambda x: x['total_traffic'], reverse=True)
        
        for i, stats in enumerate(node_stats[:10]):  # Показываем топ 10
            node = stats['node']
            status_emoji = "🟢" if node.get('isConnected', False) else "🔴"
            disabled_emoji = "⏸️" if node.get('isDisabled', False) else ""
            
            node_name = escape_markdown(node.get('name', 'Unknown'))
            message += f"{i+1}. {status_emoji}{disabled_emoji} **{node_name}**\n"
            message += f"   📍 {node.get('address')}:{node.get('port')}\n"
            message += f"   👥 Пользователей: {len(stats['users'])} (активных: {stats['active_users']})\n"
            message += f"   📊 Трафик: {format_bytes(stats['total_traffic'])}\n"
            
            if node.get('countryCode'):
                message += f"   🌍 Страна: {node.get('countryCode')}\n"
            
            message += "\n"
        
        if len(node_stats) > 10:
            message += f"... и еще {len(node_stats) - 10} серверов\n"
        
        # Общая статистика
        total_users = sum(len(stats['users']) for stats in node_stats)
        total_active = sum(stats['active_users'] for stats in node_stats)
        total_traffic = sum(stats['total_traffic'] for stats in node_stats)
        online_nodes = sum(1 for stats in node_stats if stats['node'].get('isConnected', False))
        
        message += f"\n**📈 Общая статистика:**\n"
        message += f"• Онлайн нод: {online_nodes}/{len(node_stats)}\n"
        message += f"• Всего пользователей: {total_users}\n"
        message += f"• Активных пользователей: {total_active}\n"
        message += f"• Общий трафик: {format_bytes(total_traffic)}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="nodes_usage"),
            types.InlineKeyboardButton(text="📊 Детально", callback_data="nodes_usage_detailed")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting nodes usage: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики использования.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
            ]])
        )

# ================ NODE CERTIFICATE ================

@router.callback_query(F.data == "get_panel_certificate", AuthFilter())
async def get_panel_certificate(callback: types.CallbackQuery):
    """Get panel certificate"""
    await callback.answer()
    await show_node_certificate(callback)

@router.callback_query(F.data.startswith("show_certificate:"), AuthFilter())
async def show_node_certificate_specific(callback: types.CallbackQuery):
    """Show certificate for specific node"""
    await callback.answer()
    await show_node_certificate(callback)

async def show_node_certificate(callback: types.CallbackQuery):
    """Show node certificate for copying"""
    await callback.message.edit_text("📜 Получение сертификата панели...")
    
    try:
        # Получаем сертификат панели через HTTP API
        certificate_data = await SystemAPI.get_panel_certificate()
        
        if certificate_data and certificate_data.get('publicKey'):
            pub_key = certificate_data.get('publicKey')
            
            # Определяем откуда пришел запрос
            callback_data = callback.data
            node_uuid = None
            
            if callback_data.startswith("show_certificate:"):
                node_uuid = callback_data.split(":", 1)[1]
            
            message = "📜 **Сертификат панели для ноды**\n\n"
            message += "🔐 Используйте эту переменную для настройки ноды на сервере:\n\n"
            message += f"`SSL_CERT=\"{pub_key}\"`\n\n"
            message += "💡 **Инструкция по настройке ноды:**\n"
            message += "1. Скопируйте переменную SSL_CERT выше\n"
            message += "2. Установите Remnawave Node на ваш сервер\n"
            message += "3. Добавьте эту переменную в конфигурацию\n"
            message += "4. Настройте подключение к панели\n\n"
            message += "⚠️ **Важно:** Этот ключ нужен для безопасного подключения ноды к панели!"
            
            builder = InlineKeyboardBuilder()
            if node_uuid:
                builder.row(types.InlineKeyboardButton(text="👁️ Просмотр ноды", callback_data=f"view_node:{node_uuid}"))
                builder.row(types.InlineKeyboardButton(text="🔙 К списку нод", callback_data="list_nodes"))
            else:
                builder.row(types.InlineKeyboardButton(text="🔙 К меню нод", callback_data="nodes"))
            
            await callback.message.edit_text(
                text=message,
                reply_markup=builder.as_markup()
            )
            
        else:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="get_panel_certificate"))
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes"))
            
            await callback.message.edit_text(
                "❌ Не удалось получить сертификат панели.",
                reply_markup=builder.as_markup()
            )
        
    except Exception as e:
        logger.error(f"Error showing node certificate: {e}")
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 К меню нод", callback_data="nodes"))
        
        await callback.message.edit_text(
            "❌ Ошибка при получении сертификата панели.",
            reply_markup=builder.as_markup()
        )

# ================ RESTART ALL NODES ================

@router.callback_query(F.data == "restart_all_nodes", AuthFilter())
async def restart_all_nodes_confirm(callback: types.CallbackQuery):
    """Confirm restart all nodes"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="✅ Да, перезапустить все",
        callback_data="confirm_restart_all_nodes"
    ))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="nodes"))
    
    await callback.message.edit_text(
        "⚠️ **Перезапуск всех серверов**\n\n"
        "Вы уверены, что хотите перезапустить все серверы?\n\n"
        "⚠️ Это может временно прервать соединения пользователей.",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "confirm_restart_all_nodes", AuthFilter())
async def confirm_restart_all_nodes(callback: types.CallbackQuery):
    """Confirm restart all nodes"""
    await callback.answer()
    
    try:
        # Перезапускаем все ноды через HTTP API
        response = await RemnaAPI.post("nodes/restart-all")
        
        if response:
            message = "✅ Команда на перезапуск всех серверов успешно отправлена."
        else:
            message = "❌ Ошибка при перезапуске серверов."
        
        await callback.message.edit_text(
            message,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error restarting all nodes: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при перезапуске серверов.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
            ]])
        )

# ================ ADD NEW NODE ================

@router.callback_query(F.data == "add_node", AuthFilter())
async def start_create_node(callback: types.CallbackQuery, state: FSMContext):
    """Start creating a new node"""
    await callback.answer()
    await state.clear()
    
    # Initialize node creation data
    await state.update_data(
        create_node={
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
        },
        creation_step="name"
    )
    await state.set_state(NodeStates.creating_node)
    
    message = "🆕 **Создание новой ноды**\n\n"
    message += "📝 **Шаг 1 из 4:** Введите название для новой ноды:\n\n"
    message += "💡 Например: 'VPS-Germany-1' или 'Server-Moscow'"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node"))
    
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "cancel_create_node", AuthFilter())
async def cancel_create_node(callback: types.CallbackQuery, state: FSMContext):
    """Cancel node creation"""
    await callback.answer()
    await state.clear()
    await show_nodes_menu(callback)

@router.message(StateFilter(NodeStates.creating_node), AuthFilter())
async def handle_node_creation_input(message: types.Message, state: FSMContext):
    """Handle node creation input"""
    try:
        data = await state.get_data()
        step = data.get('creation_step', 'name')
        node_data = data.get('create_node', {})
        
        user_input = message.text.strip()
        
        if step == "name":
            if len(user_input) < 3:
                await message.answer("❌ Название должно содержать минимум 3 символа. Попробуйте еще раз:")
                return
            
            node_data["name"] = user_input
            await state.update_data(create_node=node_data, creation_step="address")
            
            await message.answer(
                "🆕 **Создание новой ноды**\n\n"
                "🌐 **Шаг 2 из 4:** Введите адрес ноды:\n\n"
                "💡 Примеры:\n"
                "• `192.168.1.100`\n"
                "• `server.example.com`\n"
                "• `node1.vpn.com`",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node")
                ]])
            )
            
        elif step == "address":
            if len(user_input) < 3:
                await message.answer("❌ Адрес слишком короткий. Попробуйте еще раз:")
                return
            
            node_data["address"] = user_input
            await state.update_data(create_node=node_data, creation_step="port")
            
            await message.answer(
                "🆕 **Создание новой ноды**\n\n"
                "🔌 **Шаг 3 из 4:** Введите порт (по умолчанию 3000):\n\n"
                "💡 Обычно используется порт 3000",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="⏭️ По умолчанию (3000)", callback_data="default_port"),
                    types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node")
                ]])
            )
            
        elif step == "port":
            try:
                port = int(user_input)
                if port < 1 or port > 65535:
                    await message.answer("❌ Порт должен быть от 1 до 65535. Попробуйте еще раз:")
                    return
            except ValueError:
                await message.answer("❌ Введите корректный номер порта (число):")
                return
            
            node_data["port"] = port
            await state.update_data(create_node=node_data, creation_step="country")
            
            await message.answer(
                "🆕 **Создание новой ноды**\n\n"
                "🌍 **Шаг 4 из 4:** Введите код страны (2 символа):\n\n"
                "💡 Примеры: RU, US, DE, FR, GB",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="⏭️ Пропустить (XX)", callback_data="skip_country"),
                    types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node")
                ]])
            )
            
        elif step == "country":
            if len(user_input) != 2 or not user_input.isalpha():
                await message.answer("❌ Код страны должен состоять из 2 букв. Попробуйте еще раз:")
                return
            
            node_data["countryCode"] = user_input.upper()
            await state.update_data(create_node=node_data)
            await show_node_creation_confirmation(message, state)
        
    except Exception as e:
        logger.error(f"Error handling node creation input: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке ввода",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node")
            ]])
        )

@router.callback_query(F.data == "default_port", AuthFilter())
async def use_default_port(callback: types.CallbackQuery, state: FSMContext):
    """Use default port 3000"""
    await callback.answer()
    
    data = await state.get_data()
    node_data = data.get('create_node', {})
    node_data["port"] = 3000
    await state.update_data(create_node=node_data, creation_step="country")
    
    await callback.message.edit_text(
        "🆕 **Создание новой ноды**\n\n"
        "🌍 **Шаг 4 из 4:** Введите код страны (2 символа):\n\n"
        "💡 Примеры: RU, US, DE, FR, GB",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить (XX)", callback_data="skip_country"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node")
        ]])
    )

@router.callback_query(F.data == "skip_country", AuthFilter())
async def skip_country(callback: types.CallbackQuery, state: FSMContext):
    """Skip country input"""
    await callback.answer()
    
    data = await state.get_data()
    node_data = data.get('create_node', {})
    node_data["countryCode"] = "XX"
    await state.update_data(create_node=node_data)
    await show_node_creation_confirmation(callback.message, state)

async def show_node_creation_confirmation(message: types.Message, state: FSMContext):
    """Show node creation confirmation"""
    data = await state.get_data()
    node_data = data.get('create_node', {})
    
    confirmation_text = (
        "🆕 **Создание новой ноды - Подтверждение**\n\n"
        f"**Название:** {node_data.get('name')}\n"
        f"**Адрес:** {node_data.get('address')}\n"
        f"**Порт:** {node_data.get('port')}\n"
        f"**Страна:** {node_data.get('countryCode')}\n\n"
        "Создать ноду с указанными параметрами?"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Создать", callback_data="confirm_create_node"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_node"))
    
    try:
        await message.edit_text(
            confirmation_text,
            reply_markup=builder.as_markup()
        )
    except:
        await message.answer(
            confirmation_text,
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "confirm_create_node", AuthFilter())
async def confirm_create_node(callback: types.CallbackQuery, state: FSMContext):
    """Confirm node creation"""
    await callback.answer()
    
    data = await state.get_data()
    node_data = data.get('create_node', {})
    
    try:
        # Создаем ноду через HTTP API
        response = await RemnaAPI.post("nodes", data=node_data)
        
        if response:
            await callback.answer("✅ Нода создана успешно", show_alert=True)
            await state.clear()
            
            await callback.message.edit_text(
                f"✅ **Нода создана успешно!**\n\n"
                f"**Название:** {node_data.get('name')}\n"
                f"**Адрес:** {node_data.get('address')}:{node_data.get('port')}\n"
                f"**Страна:** {node_data.get('countryCode')}\n\n"
                "Нода готова к использованию.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="📋 К списку серверов", callback_data="list_nodes"),
                    types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при создании ноды", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        await callback.answer("❌ Ошибка при создании ноды", show_alert=True)

