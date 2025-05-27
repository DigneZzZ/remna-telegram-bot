from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from datetime import datetime, timedelta

from modules.handlers.auth import AuthFilter
from modules.handlers.states import SystemStates
from modules.api.client import RemnaAPI
from modules.api.system import SystemAPI
from modules.api.users import get_all_users, get_users_count
from modules.api.nodes import get_all_nodes

logger = logging.getLogger(__name__)

router = Router()

# ================ UTILITY FUNCTIONS ================

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = bytes_value
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    if not text:
        return ""
    
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    escaped_text = str(text)
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text

def format_datetime(dt_string: str) -> str:
    """Format datetime string to readable format"""
    if not dt_string:
        return "Не указано"
    
    try:
        clean_dt = dt_string.replace('Z', '').split('.')[0]
        dt = datetime.fromisoformat(clean_dt)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return dt_string[:19].replace('T', ' ')

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

# ================ MAIN STATS MENU ================

@router.callback_query(F.data == "stats", AuthFilter())
async def handle_stats_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle statistics menu selection"""
    await state.clear()
    await show_stats_menu(callback)

async def show_stats_menu(callback: types.CallbackQuery):
    """Show statistics menu"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Общая статистика", callback_data="system_stats"))
    builder.row(types.InlineKeyboardButton(text="📈 Статистика трафика", callback_data="bandwidth_stats"))
    builder.row(types.InlineKeyboardButton(text="🖥️ Статистика серверов", callback_data="nodes_stats"))
    builder.row(types.InlineKeyboardButton(text="👥 Статистика пользователей", callback_data="users_extended_stats"))
    builder.row(types.InlineKeyboardButton(text="⚡ Мониторинг в реальном времени", callback_data="realtime_stats"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "📊 **Статистика системы**\n\n"
    
    try:
        # Получаем быструю статистику для превью используя прямые HTTP вызовы
        users_list = await get_all_users()
        nodes_list = await get_all_nodes()
        
        if users_list:
            total_users = len(users_list)
            active_users = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
            total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            
            message += f"**📈 Быстрый обзор:**\n"
            message += f"• Пользователей: {active_users}/{total_users}\n"
            
            if nodes_list:
                online_nodes = sum(1 for node in nodes_list if node.get('isConnected', False))
                message += f"• Серверов: {online_nodes}/{len(nodes_list)}\n"
            
            message += f"• Общий трафик: {format_bytes(total_traffic)}\n\n"
        else:
            message += "**📈 Быстрый обзор:** Недоступен\n\n"
        
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        message += "**📈 Быстрый обзор:** Недоступен\n\n"
    
    message += "Выберите тип статистики:"

    await callback.answer()
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ SYSTEM STATISTICS ================

@router.callback_query(F.data == "system_stats", AuthFilter())
async def show_system_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show system statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики системы...")
    
    try:
        # Получаем системную статистику через HTTP API
        system_stats = await SystemAPI.get_stats()
        users_list = await get_all_users()
        nodes_list = await get_all_nodes()
        
        message = "📊 **Статистика системы**\n\n"
        
        # Основная информация о системе
        if system_stats:
            if system_stats.get('version'):
                message += f"**🔧 Версия системы:** {escape_markdown(system_stats.get('version'))}\n"
            if system_stats.get('uptime'):
                message += f"**⏱️ Время работы:** {format_uptime(system_stats.get('uptime'))}\n"
            if system_stats.get('lastRestart'):
                message += f"**🔄 Последний перезапуск:** {format_datetime(system_stats.get('lastRestart'))}\n"
        
        # Статистика пользователей
        if users_list:
            total_users = len(users_list)
            active_users = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
            
            message += "\n**👥 Пользователи:**\n"
            message += f"• Всего: {total_users}\n"
            message += f"• Активных: {active_users}\n"
            message += f"• Неактивных: {total_users - active_users}\n"
            
            # Статистика трафика
            total_traffic_used = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            total_traffic_limit = sum(user.get('trafficLimit', 0) or 0 for user in users_list if user.get('trafficLimit'))
            
            message += "\n**📈 Трафик:**\n"
            message += f"• Использовано: {format_bytes(total_traffic_used)}\n"
            if total_traffic_limit > 0:
                message += f"• Общий лимит: {format_bytes(total_traffic_limit)}\n"
                usage_percent = (total_traffic_used / total_traffic_limit) * 100
                message += f"• Использовано: {usage_percent:.1f}%\n"
        
        # Статистика нод
        if nodes_list:
            total_nodes = len(nodes_list)
            online_nodes = sum(1 for node in nodes_list if node.get('isConnected', False))
            
            message += "\n**🖥️ Серверы:**\n"
            message += f"• Всего: {total_nodes}\n"
            message += f"• Онлайн: {online_nodes}\n"
            message += f"• Офлайн: {total_nodes - online_nodes}\n"
        
        # Системные ресурсы (если доступно)
        if system_stats:
            if system_stats.get('cpuUsage') is not None:
                message += f"\n**💻 Ресурсы:**\n"
                message += f"• CPU: {system_stats.get('cpuUsage')}%\n"
            if system_stats.get('memoryUsage') is not None:
                message += f"• RAM: {system_stats.get('memoryUsage')}%\n"
            if system_stats.get('diskUsage') is not None:
                message += f"• Диск: {system_stats.get('diskUsage')}%\n"
        
        # Кнопки управления
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="system_stats"),
            types.InlineKeyboardButton(text="📊 Детали", callback_data="system_stats_detailed")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики системы",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
            ]])
        )

# ================ BANDWIDTH STATISTICS ================

@router.callback_query(F.data == "bandwidth_stats", AuthFilter())
async def show_bandwidth_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show bandwidth statistics"""
    await callback.answer()
    await callback.message.edit_text("📈 Загрузка статистики трафика...")
    
    try:
        # Получаем статистику трафика через HTTP API
        bandwidth_stats = await SystemAPI.get_bandwidth_stats()
        users_list = await get_all_users()
        nodes_list = await get_all_nodes()
        
        message = "📈 **Статистика трафика**\n\n"
        
        # Общая статистика трафика
        if users_list:
            total_used = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            total_limit = sum(user.get('trafficLimit', 0) or 0 for user in users_list if user.get('trafficLimit'))
            
            message += "**📊 Общая статистика:**\n"
            message += f"• Использовано всего: {format_bytes(total_used)}\n"
            if total_limit > 0:
                message += f"• Общий лимит: {format_bytes(total_limit)}\n"
                remaining = total_limit - total_used
                message += f"• Осталось: {format_bytes(remaining)}\n"
                usage_percent = (total_used / total_limit) * 100
                message += f"• Использовано: {usage_percent:.1f}%\n"
        
        # Статистика по нодам
        if nodes_list and users_list:
            message += "\n**🖥️ По серверам:**\n"
            for node in nodes_list:
                # Пользователи на этой ноде (примерное распределение)
                node_users = [user for user in users_list if user.get('nodeUuid') == node.get('uuid')]
                if not node_users:  # Если нет привязки к ноде, распределяем равномерно
                    users_per_node = len(users_list) // len(nodes_list) if nodes_list else 0
                    start_idx = nodes_list.index(node) * users_per_node
                    end_idx = start_idx + users_per_node
                    node_users = users_list[start_idx:end_idx] if start_idx < len(users_list) else []
                
                node_traffic = sum(user.get('usedTraffic', 0) or 0 for user in node_users)
                
                status_emoji = "🟢" if node.get('isConnected', False) else "🔴"
                node_name = escape_markdown(node.get('name', 'Unknown'))
                message += f"{status_emoji} **{node_name}**\n"
                message += f"  • Пользователей: {len(node_users)}\n"
                message += f"  • Трафик: {format_bytes(node_traffic)}\n"
        
        # Топ пользователей по трафику
        if users_list:
            top_users = sorted(
                [user for user in users_list if user.get('usedTraffic', 0) > 0],
                key=lambda u: u.get('usedTraffic', 0),
                reverse=True
            )[:5]
            
            if top_users:
                message += "\n**🏆 Топ пользователей по трафику:**\n"
                for i, user in enumerate(top_users, 1):
                    username = escape_markdown(user.get('username', 'Unknown'))
                    traffic = format_bytes(user.get('usedTraffic', 0))
                    message += f"{i}\\. **{username}**: {traffic}\n"
        
        # Статистика за периоды (если доступно в API)
        if bandwidth_stats:
            if bandwidth_stats.get('daily'):
                message += "\n**📅 За сегодня:**\n"
                daily = bandwidth_stats.get('daily', {})
                if daily.get('upload'):
                    message += f"• Загружено: {format_bytes(daily.get('upload'))}\n"
                if daily.get('download'):
                    message += f"• Скачано: {format_bytes(daily.get('download'))}\n"
        
        # Кнопки управления
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="bandwidth_stats"),
            types.InlineKeyboardButton(text="📊 Детали", callback_data="bandwidth_stats_detailed")
        )
        builder.row(
            types.InlineKeyboardButton(text="📈 За неделю", callback_data="bandwidth_weekly"),
            types.InlineKeyboardButton(text="📉 За месяц", callback_data="bandwidth_monthly")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting bandwidth stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики трафика",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
            ]])
        )

# ================ NODES STATISTICS ================

@router.callback_query(F.data == "nodes_stats", AuthFilter())
async def show_nodes_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show nodes statistics"""
    await callback.answer()
    await callback.message.edit_text("🖥️ Загрузка статистики серверов...")
    
    try:
        # Получаем информацию о нодах через HTTP API
        nodes_list = await get_all_nodes()
        users_list = await get_all_users()
        
        if not nodes_list:
            await callback.message.edit_text(
                "❌ Серверы не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
                ]])
            )
            return
        
        message = "🖥️ **Статистика серверов**\n\n"
        
        # Общая информация
        total_nodes = len(nodes_list)
        online_nodes = sum(1 for node in nodes_list if node.get('isConnected', False))
        
        message += f"**📊 Общая информация:**\n"
        message += f"• Всего серверов: {total_nodes}\n"
        message += f"• Онлайн: {online_nodes}\n"
        message += f"• Офлайн: {total_nodes - online_nodes}\n\n"
        
        # Детальная информация по каждой ноде
        message += "**📋 Детали серверов:**\n"
        for node in nodes_list:
            status_emoji = "🟢" if node.get('isConnected', False) else "🔴"
            
            # Пользователи на этой ноде
            node_users = [user for user in users_list if user.get('nodeUuid') == node.get('uuid')] if users_list else []
            active_users = sum(1 for user in node_users if user.get('status') == 'ACTIVE')
            node_traffic = sum(user.get('usedTraffic', 0) or 0 for user in node_users)
            
            node_name = escape_markdown(node.get('name', 'Unknown'))
            node_address = escape_markdown(node.get('address', 'Unknown'))
            
            message += f"{status_emoji} **{node_name}**\n"
            message += f"  • Адрес: `{node_address}`\n"
            message += f"  • Пользователей: {len(node_users)} \\(активных: {active_users}\\)\n"
            message += f"  • Трафик: {format_bytes(node_traffic)}\n"
            
            if node.get('isConnected'):
                # Дополнительная информация для онлайн нод
                if node.get('lastSeen'):
                    message += f"  • Последняя связь: {format_datetime(node.get('lastSeen'))}\n"
                if node.get('version'):
                    message += f"  • Версия: {escape_markdown(node.get('version'))}\n"
                if node.get('uptime'):
                    message += f"  • Uptime: {format_uptime(node.get('uptime'))}\n"
            else:
                if node.get('lastSeen'):
                    message += f"  • Офлайн с: {format_datetime(node.get('lastSeen'))}\n"
            
            message += "\n"
        
        # Кнопки управления
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="nodes_stats"),
            types.InlineKeyboardButton(text="📊 Детали", callback_data="nodes_detailed")
        )
        builder.row(
            types.InlineKeyboardButton(text="🖥️ Управление", callback_data="nodes"),
            types.InlineKeyboardButton(text="📈 Мониторинг", callback_data="nodes_monitoring")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting nodes stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики серверов",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
            ]])
        )

# ================ REAL-TIME MONITORING ================

@router.callback_query(F.data == "realtime_stats", AuthFilter())
async def show_realtime_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show real-time monitoring"""
    await callback.answer()
    await state.set_state(SystemStates.viewing_stats)
    
    try:
        # Получаем текущие данные через HTTP API
        users_list = await get_all_users()
        nodes_list = await get_all_nodes()
        
        # Текущее время
        current_time = datetime.now().strftime("%H:%M:%S")
        
        message = f"⚡ **Мониторинг в реальном времени**\n"
        message += f"🕐 Обновлено: {current_time}\n\n"
        
        # Онлайн статистика
        if users_list:
            active_users = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
            message += "**🔥 Сейчас активно:**\n"
            message += f"• Пользователей: {active_users}\n"
        
        if nodes_list:
            online_nodes = sum(1 for node in nodes_list if node.get('isConnected', False))
            message += f"• Серверов: {online_nodes}\n"
        
        # Трафик в реальном времени (активные пользователи)
        if users_list:
            recent_users = [
                user for user in users_list 
                if user.get('usedTraffic', 0) > 0 and user.get('status') == 'ACTIVE'
            ]
            
            if recent_users:
                total_active_traffic = sum(user.get('usedTraffic', 0) for user in recent_users)
                message += f"• Общий трафик активных: {format_bytes(total_active_traffic)}\n"
        
        message += "\n**📊 Статус серверов:**\n"
        if nodes_list:
            for node in nodes_list:
                status_emoji = "🟢" if node.get('isConnected', False) else "🔴"
                node_name = escape_markdown(node.get('name', 'Unknown'))
                message += f"{status_emoji} {node_name}\n"
        else:
            message += "Серверы не найдены\n"
        
        # Последние события
        message += "\n**📝 Последние события:**\n"
        message += "• Мониторинг активности\\.\\.\\.\n"
        
        # Кнопки управления
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="realtime_stats"),
            types.InlineKeyboardButton(text="⏸️ Пауза", callback_data="pause_monitoring")
        )
        builder.row(
            types.InlineKeyboardButton(text="📊 Графики", callback_data="stats_charts"),
            types.InlineKeyboardButton(text="⚠️ Алерты", callback_data="stats_alerts")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting realtime stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении мониторинга",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
            ]])
        )

# ================ DETAILED STATISTICS ================

@router.callback_query(F.data == "system_stats_detailed", AuthFilter())
async def show_system_stats_detailed(callback: types.CallbackQuery):
    """Show detailed system statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка детальной статистики...")
    
    try:
        # Получаем детальную статистику через HTTP API
        system_stats = await SystemAPI.get_stats()
        users_list = await get_all_users()
        nodes_list = await get_all_nodes()
        
        message = "📊 **Детальная статистика системы**\n\n"
        
        if users_list:
            # Расширенная информация о пользователях
            now = datetime.now()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            new_users_week = 0
            new_users_month = 0
            expired_users = 0
            
            for user in users_list:
                # Новые пользователи
                created_at = user.get('createdAt')
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if created_date > week_ago:
                            new_users_week += 1
                        if created_date > month_ago:
                            new_users_month += 1
                    except Exception:
                        pass
                
                # Истекшие пользователи
                expire_at = user.get('expireAt')
                if expire_at:
                    try:
                        expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                        if expire_date < now:
                            expired_users += 1
                    except Exception:
                        pass
            
            message += "**👥 Детальная статистика пользователей:**\n"
            message += f"• Новых за неделю: {new_users_week}\n"
            message += f"• Новых за месяц: {new_users_month}\n"
            message += f"• Истекших: {expired_users}\n"
            
            # Распределение по лимитам трафика
            unlimited_users = sum(1 for user in users_list if not user.get('trafficLimit'))
            limited_users = len(users_list) - unlimited_users
            
            message += f"• С лимитом трафика: {limited_users}\n"
            message += f"• Безлимитных: {unlimited_users}\n"
            
            # Средние показатели
            if users_list:
                avg_traffic = sum(user.get('usedTraffic', 0) or 0 for user in users_list) / len(users_list)
                message += f"• Средний трафик: {format_bytes(int(avg_traffic))}\n"
        
        # Статистика по нодам
        if nodes_list and users_list:
            message += "\n**🖥️ Детальная статистика серверов:**\n"
            for node in nodes_list:
                node_users = [user for user in users_list if user.get('nodeUuid') == node.get('uuid')]
                active_users = sum(1 for user in node_users if user.get('status') == 'ACTIVE')
                node_traffic = sum(user.get('usedTraffic', 0) or 0 for user in node_users)
                
                max_users = node.get('maxUsers', 100)
                load_percent = (len(node_users) / max(max_users, 1)) * 100
                
                node_name = escape_markdown(node.get('name', 'Unknown'))
                message += f"**{node_name}:**\n"
                message += f"  • Загрузка: {load_percent:.1f}%\n"
                message += f"  • Активных: {active_users}/{len(node_users)}\n"
                message += f"  • Трафик: {format_bytes(node_traffic)}\n"
        
        # Системные ресурсы (если доступно)
        if system_stats:
            message += "\n**💻 Системные ресурсы:**\n"
            if system_stats.get('cpuUsage') is not None:
                message += f"• CPU: {system_stats.get('cpuUsage')}%\n"
            if system_stats.get('memoryUsage') is not None:
                message += f"• RAM: {system_stats.get('memoryUsage')}%\n"
            if system_stats.get('diskUsage') is not None:
                message += f"• Диск: {system_stats.get('diskUsage')}%\n"
            if system_stats.get('networkConnections') is not None:
                message += f"• Сетевые соединения: {system_stats.get('networkConnections')}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="system_stats_detailed"),
            types.InlineKeyboardButton(text="📊 Обычная", callback_data="system_stats")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting detailed system stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении детальной статистики",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="system_stats")
            ]])
        )

# ================ BANDWIDTH PERIOD STATISTICS ================

@router.callback_query(F.data == "bandwidth_weekly", AuthFilter())
async def show_bandwidth_weekly(callback: types.CallbackQuery):
    """Show weekly bandwidth statistics"""
    await callback.answer()
    
    try:
        users_list = await get_all_users()
        
        message = "📈 **Статистика трафика за неделю**\n\n"
        
        if users_list:
            # Расчет за последние 7 дней
            total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            
            message += f"**📊 Общий трафик:**\n"
            message += f"• За неделю: {format_bytes(total_traffic)}\n"
            message += f"• В среднем в день: {format_bytes(total_traffic // 7)}\n"
            
            # Топ пользователей за неделю
            top_users = sorted(
                [user for user in users_list if user.get('usedTraffic', 0) > 0],
                key=lambda u: u.get('usedTraffic', 0),
                reverse=True
            )[:10]
            
            if top_users:
                message += "\n**🏆 Топ 10 за неделю:**\n"
                for i, user in enumerate(top_users, 1):
                    username = escape_markdown(user.get('username', 'Unknown'))
                    traffic = format_bytes(user.get('usedTraffic', 0))
                    message += f"{i}\\. {username}: {traffic}\n"
        else:
            message += "Данные о пользователях недоступны\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="📉 За месяц", callback_data="bandwidth_monthly"),
            types.InlineKeyboardButton(text="📊 Общая", callback_data="bandwidth_stats")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bandwidth_stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting weekly bandwidth: {e}")
        await callback.answer("❌ Ошибка при получении статистики", show_alert=True)

@router.callback_query(F.data == "bandwidth_monthly", AuthFilter())
async def show_bandwidth_monthly(callback: types.CallbackQuery):
    """Show monthly bandwidth statistics"""
    await callback.answer()
    
    try:
        users_list = await get_all_users()
        
        message = "📉 **Статистика трафика за месяц**\n\n"
        
        if users_list:
            # Расчет за последние 30 дней
            total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            
            message += f"**📊 Общий трафик:**\n"
            message += f"• За месяц: {format_bytes(total_traffic)}\n"
            message += f"• В среднем в день: {format_bytes(total_traffic // 30)}\n"
            message += f"• В среднем в неделю: {format_bytes(total_traffic // 4)}\n"
            
            # Прогноз на следующий месяц
            projected = total_traffic * 2  # Простой прогноз
            message += f"• Прогноз на след\\. месяц: {format_bytes(projected)}\n"
        else:
            message += "Данные о пользователях недоступны\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="📈 За неделю", callback_data="bandwidth_weekly"),
            types.InlineKeyboardButton(text="📊 Общая", callback_data="bandwidth_stats")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bandwidth_stats"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting monthly bandwidth: {e}")
        await callback.answer("❌ Ошибка при получении статистики", show_alert=True)

# ================ PLACEHOLDER HANDLERS ================

@router.callback_query(F.data.startswith(("bandwidth_stats_detailed", "nodes_detailed", "nodes_monitoring", "pause_monitoring", "stats_charts", "stats_alerts")), AuthFilter())
async def handle_stats_placeholder(callback: types.CallbackQuery):
    """Placeholder for advanced statistics features"""
    await callback.answer()
    
    feature_names = {
        "bandwidth_stats_detailed": "Детальная статистика трафика",
        "nodes_detailed": "Детальная статистика серверов", 
        "nodes_monitoring": "Мониторинг серверов",
        "pause_monitoring": "Приостановка мониторинга",
        "stats_charts": "Графики статистики",
        "stats_alerts": "Алерты статистики"
    }
    
    feature_name = feature_names.get(callback.data, "Функция")
    
    await callback.message.edit_text(
        f"📊 **{feature_name}**\n\n"
        f"🔧 Функция в разработке\n\n"
        f"Планируется реализация:\n"
        f"• Расширенная аналитика\n"
        f"• Интерактивные графики\n"
        f"• Система уведомлений\n"
        f"• Экспорт отчетов",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
        ]])
    )

# ================ BACK NAVIGATION ================

@router.callback_query(F.data == "back_to_stats", AuthFilter())
async def back_to_stats(callback: types.CallbackQuery, state: FSMContext):
    """Return to stats menu"""
    await show_stats_menu(callback)

logger.info("Stats handlers module loaded successfully (SDK-free version)")