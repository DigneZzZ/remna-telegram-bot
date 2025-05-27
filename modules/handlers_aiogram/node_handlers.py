from aiogram import Router, types, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import logging
import re

from modules.handlers_aiogram.auth import AuthFilter
from modules.handlers_aiogram.states import NodeStates
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown, format_node_details
)

logger = logging.getLogger(__name__)

router = Router()

# ================ MAIN NODES MENU ================

@router.callback_query(Text("nodes"), AuthFilter())
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
        # Получаем быструю статистику для превью
        sdk = RemnaAPI.get_sdk()
        nodes_response = await sdk.nodes.get_all_nodes()
        
        if nodes_response:
            total_nodes = len(nodes_response)
            online_nodes = sum(1 for node in nodes_response if node.is_connected)
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

@router.callback_query(Text("list_nodes"), AuthFilter())
async def list_nodes(callback: types.CallbackQuery, state: FSMContext):
    """List all nodes"""
    await callback.answer()
    await callback.message.edit_text("🖥️ Загрузка списка серверов...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        nodes_response = await sdk.nodes.get_all_nodes()
        
        if not nodes_response:
            await callback.message.edit_text(
                "❌ Серверы не найдены или ошибка при получении списка.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
                ]])
            )
            return
        
        # Store nodes data in state
        nodes_dict = {node.uuid: node.model_dump() for node in nodes_response}
        await state.update_data(nodes=nodes_dict, page=0)
        await state.set_state(NodeStates.selecting_node)
        
        # Count online/offline nodes
        online_count = sum(1 for node in nodes_response if node.is_connected)
        total_count = len(nodes_response)
        
        message = f"🖥️ **Список серверов** ({online_count}/{total_count} онлайн)\n\n"
        
        # Show first 8 nodes
        builder = InlineKeyboardBuilder()
        for i, node in enumerate(nodes_response[:8]):
            status_emoji = "🟢" if node.is_connected else "🔴"
            disabled_emoji = "⏸️" if getattr(node, 'is_disabled', False) else ""
            
            button_text = f"{status_emoji}{disabled_emoji} {node.name}"
            builder.row(types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_node:{node.uuid}"
            ))
        
        # Pagination if needed
        if len(nodes_response) > 8:
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

@router.callback_query(Text(startswith="nodes_page:"), AuthFilter())
async def handle_node_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle node list pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    nodes_dict = data.get('nodes', {})
    
    if not nodes_dict:
        await callback.answer("❌ Данные серверов не найдены", show_alert=True)
        return
    
    nodes_list = list(nodes_dict.values())
    items_per_page = 8
    total_pages = (len(nodes_list) + items_per_page - 1) // items_per_page
    
    if page < 0 or page >= total_pages:
        await callback.answer("❌ Неверная страница", show_alert=True)
        return
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_nodes = nodes_list[start_idx:end_idx]
    
    online_count = sum(1 for node in nodes_list if node.get('is_connected', False))
    total_count = len(nodes_list)
    
    message = f"🖥️ **Список серверов** ({online_count}/{total_count} онлайн)\n"
    message += f"Страница {page + 1} из {total_pages}\n\n"
    
    builder = InlineKeyboardBuilder()
    for node in page_nodes:
        status_emoji = "🟢" if node.get('is_connected', False) else "🔴"
        disabled_emoji = "⏸️" if node.get('is_disabled', False) else ""
        
        button_text = f"{status_emoji}{disabled_emoji} {node.get('name', 'Unknown')}"
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

@router.callback_query(Text(startswith="view_node:"), AuthFilter())
async def show_node_details(callback: types.CallbackQuery, state: FSMContext):
    """Show node details"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        node = await sdk.nodes.get_node_by_id(node_uuid)
        
        if not node:
            await callback.message.edit_text(
                "❌ Сервер не найден или ошибка при получении данных.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_nodes")
                ]])
            )
            return
        
        # Store current node in state
        await state.update_data(current_node=node.model_dump())
        await state.set_state(NodeStates.viewing_node)
        
        # Format node details
        node_data = node.model_dump()
        message = format_node_details(node_data)
        
        # Create action buttons
        builder = InlineKeyboardBuilder()
        
        # Status control
        if getattr(node, 'is_disabled', False):
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

@router.callback_query(Text(startswith="enable_node:"), AuthFilter())
async def enable_node(callback: types.CallbackQuery, state: FSMContext):
    """Enable node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.nodes.enable_node(node_uuid)
        
        if success:
            await callback.answer("✅ Сервер включен", show_alert=True)
            # Refresh node details
            await show_node_details(callback, state)
        else:
            await callback.answer("❌ Ошибка при включении сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error enabling node: {e}")
        await callback.answer("❌ Ошибка при включении сервера", show_alert=True)

@router.callback_query(Text(startswith="disable_node:"), AuthFilter())
async def disable_node(callback: types.CallbackQuery, state: FSMContext):
    """Disable node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.nodes.disable_node(node_uuid)
        
        if success:
            await callback.answer("✅ Сервер отключен", show_alert=True)
            # Refresh node details
            await show_node_details(callback, state)
        else:
            await callback.answer("❌ Ошибка при отключении сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error disabling node: {e}")
        await callback.answer("❌ Ошибка при отключении сервера", show_alert=True)

@router.callback_query(Text(startswith="restart_node:"), AuthFilter())
async def restart_node(callback: types.CallbackQuery, state: FSMContext):
    """Restart node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.nodes.restart_node(node_uuid)
        
        if success:
            await callback.answer("✅ Команда на перезапуск отправлена", show_alert=True)
        else:
            await callback.answer("❌ Ошибка при перезапуске сервера", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error restarting node: {e}")
        await callback.answer("❌ Ошибка при перезапуске сервера", show_alert=True)

@router.callback_query(Text(startswith="refresh_node:"), AuthFilter())
async def refresh_node(callback: types.CallbackQuery, state: FSMContext):
    """Refresh node details"""
    await callback.answer("🔄 Обновление данных...")
    await show_node_details(callback, state)

@router.callback_query(Text(startswith="delete_node:"), AuthFilter())
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

@router.callback_query(Text(startswith="confirm_delete_node:"), AuthFilter())
async def confirm_delete_node(callback: types.CallbackQuery, state: FSMContext):
    """Confirm node deletion"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.nodes.delete_node(node_uuid)
        
        if success:
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

@router.callback_query(Text(startswith="node_stats:"), AuthFilter())
async def show_node_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show node statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики сервера...")
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем информацию о ноде
        node = await sdk.nodes.get_node_by_id(node_uuid)
        if not node:
            await callback.message.edit_text(
                "❌ Сервер не найден.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_node:{node_uuid}")
                ]])
            )
            return
        
        message = f"📊 **Статистика сервера {escape_markdown(node.name)}**\n\n"
        
        # Основная информация
        status = "🟢 Включен" if not getattr(node, 'is_disabled', False) else "🔴 Отключен"
        connection = "✅ Подключен" if node.is_connected else "❌ Не подключен"
        
        message += f"🖥️ **Статус:** {status}\n"
        message += f"🔌 **Соединение:** {connection}\n"
        message += f"🌍 **Страна:** {getattr(node, 'country_code', 'N/A')}\n"
        message += f"📍 **Адрес:** {node.address}:{node.port}\n\n"
        
        # Статистика пользователей на ноде
        try:
            users_response = await sdk.users.get_all_users_v2()
            if users_response and users_response.users:
                node_users = [user for user in users_response.users if getattr(user, 'node_uuid', None) == node_uuid]
                active_users = sum(1 for user in node_users if user.is_active)
                total_traffic = sum(user.used_traffic or 0 for user in node_users)
                
                message += f"👥 **Пользователи на ноде:**\n"
                message += f"  • Всего: {len(node_users)}\n"
                message += f"  • Активных: {active_users}\n"
                message += f"  • Общий трафик: {format_bytes(total_traffic)}\n\n"
        except Exception as e:
            logger.warning(f"Could not get users stats for node: {e}")
        
        # Статистика трафика ноды
        if hasattr(node, 'traffic_used_bytes') and hasattr(node, 'traffic_limit_bytes'):
            used = getattr(node, 'traffic_used_bytes', 0)
            limit = getattr(node, 'traffic_limit_bytes', 0)
            
            message += f"📈 **Трафик ноды:**\n"
            message += f"  • Использовано: {format_bytes(used)}\n"
            if limit > 0:
                message += f"  • Лимит: {format_bytes(limit)}\n"
                usage_percent = (used / limit) * 100 if limit > 0 else 0
                message += f"  • Использовано: {usage_percent:.1f}%\n"
            message += "\n"
        
        # Дополнительная информация
        if hasattr(node, 'last_seen') and node.last_seen:
            message += f"🕐 **Последняя активность:** {format_datetime(node.last_seen)}\n"
        
        if hasattr(node, 'version') and node.version:
            message += f"🔧 **Версия:** {node.version}\n"
        
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

@router.callback_query(Text("nodes_usage"), AuthFilter())
async def show_nodes_usage(callback: types.CallbackQuery, state: FSMContext):
    """Show nodes usage statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики использования серверов...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем все ноды
        nodes_response = await sdk.nodes.get_all_nodes()
        if not nodes_response:
            await callback.message.edit_text(
                "❌ Серверы не найдены.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes")
                ]])
            )
            return
        
        # Получаем статистику пользователей для подсчета трафика
        users_response = await sdk.users.get_all_users_v2()
        users_by_node = {}
        
        if users_response and users_response.users:
            for user in users_response.users:
                node_uuid = getattr(user, 'node_uuid', None)
                if node_uuid:
                    if node_uuid not in users_by_node:
                        users_by_node[node_uuid] = []
                    users_by_node[node_uuid].append(user)
        
        message = f"📊 **Статистика использования серверов**\n\n"
        
        # Сортируем ноды по трафику
        node_stats = []
        for node in nodes_response:
            node_users = users_by_node.get(node.uuid, [])
            total_traffic = sum(user.used_traffic or 0 for user in node_users)
            active_users = sum(1 for user in node_users if user.is_active)
            
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
            status_emoji = "🟢" if node.is_connected else "🔴"
            disabled_emoji = "⏸️" if getattr(node, 'is_disabled', False) else ""
            
            message += f"{i+1}. {status_emoji}{disabled_emoji} **{escape_markdown(node.name)}**\n"
            message += f"   📍 {node.address}:{node.port}\n"
            message += f"   👥 Пользователей: {len(stats['users'])} (активных: {stats['active_users']})\n"
            message += f"   📊 Трафик: {format_bytes(stats['total_traffic'])}\n"
            
            if hasattr(node, 'country_code'):
                message += f"   🌍 Страна: {node.country_code}\n"
            
            message += "\n"
        
        if len(node_stats) > 10:
            message += f"... и еще {len(node_stats) - 10} серверов\n"
        
        # Общая статистика
        total_users = sum(len(stats['users']) for stats in node_stats)
        total_active = sum(stats['active_users'] for stats in node_stats)
        total_traffic = sum(stats['total_traffic'] for stats in node_stats)
        online_nodes = sum(1 for stats in node_stats if stats['node'].is_connected)
        
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

@router.callback_query(Text("get_panel_certificate"), AuthFilter())
async def get_panel_certificate(callback: types.CallbackQuery):
    """Get panel certificate"""
    await callback.answer()
    await show_node_certificate(callback)

@router.callback_query(Text(startswith="show_certificate:"), AuthFilter())
async def show_node_certificate_specific(callback: types.CallbackQuery):
    """Show certificate for specific node"""
    await callback.answer()
    await show_node_certificate(callback)

async def show_node_certificate(callback: types.CallbackQuery):
    """Show node certificate for copying"""
    await callback.message.edit_text("📜 Получение сертификата панели...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем сертификат панели
        certificate_data = await sdk.system.get_panel_certificate()
        
        if certificate_data and hasattr(certificate_data, 'public_key'):
            pub_key = certificate_data.public_key
            
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

@router.callback_query(Text("restart_all_nodes"), AuthFilter())
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

@router.callback_query(Text("confirm_restart_all_nodes"), AuthFilter())
async def confirm_restart_all_nodes(callback: types.CallbackQuery):
    """Confirm restart all nodes"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.nodes.restart_all_nodes()
        
        if success:
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

@router.callback_query(Text("add_node"), AuthFilter())
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
            "is_traffic_tracking_active": False,
            "traffic_limit_bytes": 0,
            "notify_percent": 80,
            "traffic_reset_day": 1,
            "excluded_inbounds": [],
            "country_code": "XX",
            "consumption_multiplier": 1.0
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

@router.callback_query(Text("cancel_create_node"), AuthFilter())
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
            
            node_data["country_code"] = user_input.upper()
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

@router.callback_query(Text("default_port"), AuthFilter())
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

@router.callback_query(Text("skip_country"), AuthFilter())
async def skip_country(callback: types.CallbackQuery, state: FSMContext):
    """Skip country input"""
    await callback.answer()
    
    data = await state.get_data()
    node_data = data.get('create_node', {})
    node_data["country_code"] = "XX"
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
        f"**Страна:** {node_data.get('country_code')}\n\n"
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

@router.callback_query(Text("confirm_create_node"), AuthFilter())
async def confirm_create_node(callback: types.CallbackQuery, state: FSMContext):
    """Confirm node creation"""
    await callback.answer()
    
    data = await state.get_data()
    node_data = data.get('create_node', {})
    
    try:
        # Create node using SDK
        sdk = RemnaAPI.get_sdk()
        success = await sdk.nodes.create_node(**node_data)
        
        if success:
            await callback.answer("✅ Нода создана успешно", show_alert=True)
            await state.clear()
            
            await callback.message.edit_text(
                f"✅ **Нода создана успешно!**\n\n"
                f"**Название:** {node_data.get('name')}\n"
                f"**Адрес:** {node_data.get('address')}:{node_data.get('port')}\n"
                f"**Страна:** {node_data.get('country_code')}\n\n"
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

# ================ EDIT NODE ================

@router.callback_query(Text(startswith="edit_node:"), AuthFilter())
async def edit_node(callback: types.CallbackQuery, state: FSMContext):
    """Edit node"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    # For now, redirect to view node (edit functionality can be added later)
    await callback.message.edit_text(
        "📝 **Редактирование ноды**\n\n"
        "⚠️ Функция редактирования ноды пока недоступна.\n"
        "Используйте удаление и создание новой ноды.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад к серверу", callback_data=f"view_node:{node_uuid}")
        ]])
    )

# ================ DETAILED NODE STATISTICS ================

@router.callback_query(Text(startswith="node_stats_detailed:"), AuthFilter())
async def show_node_stats_detailed(callback: types.CallbackQuery):
    """Show detailed node statistics"""
    await callback.answer()
    
    node_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        node = await sdk.nodes.get_node_by_id(node_uuid)
        
        if not node:
            await callback.answer("❌ Сервер не найден", show_alert=True)
            return
        
        message = f"📊 **Детальная статистика сервера {escape_markdown(node.name)}**\n\n"
        
        # Основная информация
        message += f"🖥️ **Основная информация:**\n"
        message += f"• UUID: `{node.uuid}`\n"
        message += f"• Адрес: {node.address}:{node.port}\n"
        message += f"• Страна: {getattr(node, 'country_code', 'N/A')}\n"
        message += f"• Статус: {'🟢 Включен' if not getattr(node, 'is_disabled', False) else '🔴 Отключен'}\n"
        message += f"• Соединение: {'✅ Подключен' if node.is_connected else '❌ Не подключен'}\n\n"
        
        # Расширенная информация
        if hasattr(node, 'created_at') and node.created_at:
            message += f"📅 **Создана:** {format_datetime(node.created_at)}\n"
        
        if hasattr(node, 'last_seen') and node.last_seen:
            message += f"🕐 **Последняя активность:** {format_datetime(node.last_seen)}\n"
        
        if hasattr(node, 'version') and node.version:
            message += f"🔧 **Версия:** {node.version}\n"
        
        # Настройки трафика
        if hasattr(node, 'is_traffic_tracking_active'):
            message += f"\n📈 **Настройки трафика:**\n"
            message += f"• Отслеживание: {'✅ Включено' if node.is_traffic_tracking_active else '❌ Отключено'}\n"
            
            if hasattr(node, 'traffic_limit_bytes') and node.traffic_limit_bytes > 0:
                message += f"• Лимит: {format_bytes(node.traffic_limit_bytes)}\n"
                
                if hasattr(node, 'traffic_used_bytes'):
                    used = node.traffic_used_bytes
                    limit = node.traffic_limit_bytes
                    usage_percent = (used / limit) * 100 if limit > 0 else 0
                    message += f"• Использовано: {format_bytes(used)} ({usage_percent:.1f}%)\n"
        
        # Статистика пользователей
        try:
            users_response = await sdk.users.get_all_users_v2()
            if users_response and users_response.users:
                node_users = [user for user in users_response.users if getattr(user, 'node_uuid', None) == node_uuid]
                
                message += f"\n👥 **Статистика пользователей:**\n"
                message += f"• Всего пользователей: {len(node_users)}\n"
                
                if node_users:
                    active_users = sum(1 for user in node_users if user.is_active)
                    inactive_users = len(node_users) - active_users
                    total_traffic = sum(user.used_traffic or 0 for user in node_users)
                    
                    message += f"• Активных: {active_users}\n"
                    message += f"• Неактивных: {inactive_users}\n"
                    message += f"• Общий трафик пользователей: {format_bytes(total_traffic)}\n"
                    
                    # Средний трафик на пользователя
                    if len(node_users) > 0:
                        avg_traffic = total_traffic / len(node_users)
                        message += f"• Средний трафик на пользователя: {format_bytes(int(avg_traffic))}\n"
        except Exception as e:
            logger.warning(f"Could not get detailed users stats for node: {e}")
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"node_stats_detailed:{node_uuid}"),
            types.InlineKeyboardButton(text="📊 Обычная", callback_data=f"node_stats:{node_uuid}")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к серверу", callback_data=f"view_node:{node_uuid}"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting detailed node statistics: {e}")
        await callback.answer("❌ Ошибка при получении детальной статистики", show_alert=True)

@router.callback_query(Text("nodes_usage_detailed"), AuthFilter())
async def show_nodes_usage_detailed(callback: types.CallbackQuery):
    """Show detailed nodes usage statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка детальной статистики серверов...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем все ноды
        nodes_response = await sdk.nodes.get_all_nodes()
        if not nodes_response:
            await callback.message.edit_text(
                "❌ Серверы не найдены.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes_usage")
                ]])
            )
            return
        
        # Получаем статистику пользователей
        users_response = await sdk.users.get_all_users_v2()
        users_by_node = {}
        
        if users_response and users_response.users:
            for user in users_response.users:
                node_uuid = getattr(user, 'node_uuid', None)
                if node_uuid:
                    if node_uuid not in users_by_node:
                        users_by_node[node_uuid] = []
                    users_by_node[node_uuid].append(user)
        
        message = f"📊 **Детальная статистика использования серверов**\n\n"
        
        # Анализируем каждую ноду детально
        total_nodes = len(nodes_response)
        online_nodes = sum(1 for node in nodes_response if node.is_connected)
        
        message += f"**📈 Общий обзор:**\n"
        message += f"• Всего серверов: {total_nodes}\n"
        message += f"• Онлайн: {online_nodes}\n"
        message += f"• Офлайн: {total_nodes - online_nodes}\n\n"
        
        # Группируем по статусу
        online_nodes_list = [node for node in nodes_response if node.is_connected]
        offline_nodes_list = [node for node in nodes_response if not node.is_connected]
        
        # Онлайн серверы
        if online_nodes_list:
            message += "🟢 **Онлайн серверы:**\n"
            for node in online_nodes_list:
                node_users = users_by_node.get(node.uuid, [])
                active_users = sum(1 for user in node_users if user.is_active)
                total_traffic = sum(user.used_traffic or 0 for user in node_users)
                
                message += f"• **{escape_markdown(node.name)}** ({node.address}:{node.port})\n"
                message += f"  👥 {len(node_users)} польз. (акт: {active_users}) | 📊 {format_bytes(total_traffic)}\n"
            message += "\n"
        
        # Офлайн серверы
        if offline_nodes_list:
            message += "🔴 **Офлайн серверы:**\n"
            for node in offline_nodes_list:
                node_users = users_by_node.get(node.uuid, [])
                message += f"• **{escape_markdown(node.name)}** ({node.address}:{node.port})\n"
                message += f"  👥 {len(node_users)} пользователей\n"
            message += "\n"
        
        # Общая статистика
        total_users = sum(len(users) for users in users_by_node.values())
        total_active = sum(
            sum(1 for user in users if user.is_active) 
            for users in users_by_node.values()
        )
        total_traffic = sum(
            sum(user.used_traffic or 0 for user in users)
            for users in users_by_node.values()
        )
        
        message += f"**📊 Итоговая статистика:**\n"
        message += f"• Всего пользователей: {total_users}\n"
        message += f"• Активных пользователей: {total_active}\n"
        message += f"• Общий трафик: {format_bytes(total_traffic)}\n"
        
        if total_users > 0:
            avg_users_per_node = total_users / total_nodes
            message += f"• Среднее пользователей на сервер: {avg_users_per_node:.1f}\n"
        
        if total_traffic > 0 and total_users > 0:
            avg_traffic_per_user = total_traffic / total_users
            message += f"• Средний трафик на пользователя: {format_bytes(int(avg_traffic_per_user))}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="nodes_usage_detailed"),
            types.InlineKeyboardButton(text="📊 Обычная", callback_data="nodes_usage")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting detailed nodes usage: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении детальной статистики.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="nodes_usage")
            ]])
        )