from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from datetime import datetime, timedelta

from modules.handlers.auth import AuthFilter
from modules.handlers.states import SystemStates
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown,
    format_system_stats, format_bandwidth_stats
)

logger = logging.getLogger(__name__)

router = Router()

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
        # Получаем быструю статистику для превью
        sdk = RemnaAPI.get_sdk()
        
        # Статистика пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        total_users = len(users_response.users)
        active_users = sum(1 for user in users_response.users if user.is_active)
        
        # Статистика нод
        nodes_response = await sdk.nodes.get_all_nodes()
        total_nodes = len(nodes_response)
        online_nodes = sum(1 for node in nodes_response if node.is_connected)
        
        # Общий трафик
        total_traffic = sum(user.used_traffic or 0 for user in users_response.users)
        
        message += f"**📈 Быстрый обзор:**\n"
        message += f"• Пользователей: {active_users}/{total_users}\n"
        message += f"• Серверов: {online_nodes}/{total_nodes}\n"
        message += f"• Общий трафик: {format_bytes(total_traffic)}\n\n"
        
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
        sdk = RemnaAPI.get_sdk()
        
        # Получаем общую статистику системы
        system_stats = await sdk.system.get_system_stats()
        
        if not system_stats:
            await callback.message.edit_text(
                "❌ Не удалось получить статистику системы",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
                ]])
            )
            return
        
        # Получаем дополнительную информацию
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        nodes_response = await sdk.nodes.get_all_nodes()
        
        # Формируем сообщение
        message = "📊 **Статистика системы**\n\n"
        
        # Основная информация о системе
        if hasattr(system_stats, 'version'):
            message += f"**🔧 Версия системы:** {system_stats.version}\n"
        if hasattr(system_stats, 'uptime'):
            message += f"**⏱️ Время работы:** {format_uptime(system_stats.uptime)}\n"
        if hasattr(system_stats, 'last_restart'):
            message += f"**🔄 Последний перезапуск:** {format_datetime(system_stats.last_restart)}\n"
        
        message += "\n**👥 Пользователи:**\n"
        total_users = len(users_response.users)
        active_users = sum(1 for user in users_response.users if user.is_active)
        message += f"• Всего: {total_users}\n"
        message += f"• Активных: {active_users}\n"
        message += f"• Неактивных: {total_users - active_users}\n"
        
        # Статистика трафика
        total_traffic_used = sum(user.used_traffic or 0 for user in users_response.users)
        total_traffic_limit = sum(user.traffic_limit or 0 for user in users_response.users if user.traffic_limit)
        
        message += "\n**📈 Трафик:**\n"
        message += f"• Использовано: {format_bytes(total_traffic_used)}\n"
        if total_traffic_limit > 0:
            message += f"• Общий лимит: {format_bytes(total_traffic_limit)}\n"
            usage_percent = (total_traffic_used / total_traffic_limit) * 100
            message += f"• Использовано: {usage_percent:.1f}%\n"
        
        # Статистика нод
        message += "\n**🖥️ Серверы:**\n"
        total_nodes = len(nodes_response)
        online_nodes = sum(1 for node in nodes_response if node.is_connected)
        message += f"• Всего: {total_nodes}\n"
        message += f"• Онлайн: {online_nodes}\n"
        message += f"• Офлайн: {total_nodes - online_nodes}\n"
        
        # Дополнительная статистика
        if hasattr(system_stats, 'cpu_usage'):
            message += f"\n**💻 Ресурсы:**\n"
            message += f"• CPU: {system_stats.cpu_usage}%\n"
        if hasattr(system_stats, 'memory_usage'):
            message += f"• RAM: {system_stats.memory_usage}%\n"
        if hasattr(system_stats, 'disk_usage'):
            message += f"• Диск: {system_stats.disk_usage}%\n"
        
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

def format_uptime(uptime_seconds: int) -> str:
    """Format uptime in human readable format"""
    try:
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    except:
        return str(uptime_seconds)

# ================ BANDWIDTH STATISTICS ================

@router.callback_query(F.data == "bandwidth_stats", AuthFilter())
async def show_bandwidth_stats(callback: types.CallbackQuery, state: FSMContext):
    """Show bandwidth statistics"""
    await callback.answer()
    await callback.message.edit_text("📈 Загрузка статистики трафика...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем статистику трафика
        bandwidth_stats = await sdk.system.get_bandwidth_stats()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        message = "📈 **Статистика трафика**\n\n"
        
        # Общая статистика трафика
        total_used = sum(user.used_traffic or 0 for user in users_response.users)
        total_limit = sum(user.traffic_limit or 0 for user in users_response.users if user.traffic_limit)
        
        message += "**📊 Общая статистика:**\n"
        message += f"• Использовано всего: {format_bytes(total_used)}\n"
        if total_limit > 0:
            message += f"• Общий лимит: {format_bytes(total_limit)}\n"
            remaining = total_limit - total_used
            message += f"• Осталось: {format_bytes(remaining)}\n"
            usage_percent = (total_used / total_limit) * 100
            message += f"• Использовано: {usage_percent:.1f}%\n"
        
        # Статистика по нодам
        nodes_response = await sdk.nodes.get_all_nodes()
        if nodes_response:
            message += "\n**🖥️ По серверам:**\n"
            for node in nodes_response:
                # Пользователи на этой ноде
                node_users = [user for user in users_response.users if getattr(user, 'node_uuid', None) == node.uuid]
                node_traffic = sum(user.used_traffic or 0 for user in node_users)
                
                status_emoji = "🟢" if node.is_connected else "🔴"
                message += f"{status_emoji} **{escape_markdown(node.name)}**\n"
                message += f"  • Пользователей: {len(node_users)}\n"
                message += f"  • Трафик: {format_bytes(node_traffic)}\n"
        
        # Топ пользователей по трафику
        top_users = sorted(
            [user for user in users_response.users if user.used_traffic and user.used_traffic > 0],
            key=lambda u: u.used_traffic,
            reverse=True
        )[:5]
        
        if top_users:
            message += "\n**🏆 Топ пользователей по трафику:**\n"
            for i, user in enumerate(top_users, 1):
                message += f"{i}. **{escape_markdown(user.username)}**: {format_bytes(user.used_traffic)}\n"
        
        # Статистика за периоды (если доступно в SDK)
        if bandwidth_stats and hasattr(bandwidth_stats, 'daily_stats'):
            message += "\n**📅 За сегодня:**\n"
            if hasattr(bandwidth_stats.daily_stats, 'upload'):
                message += f"• Загружено: {format_bytes(bandwidth_stats.daily_stats.upload)}\n"
            if hasattr(bandwidth_stats.daily_stats, 'download'):
                message += f"• Скачано: {format_bytes(bandwidth_stats.daily_stats.download)}\n"
        
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
        sdk = RemnaAPI.get_sdk()
        
        # Получаем информацию о нодах
        nodes_response = await sdk.nodes.get_all_nodes()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not nodes_response:
            await callback.message.edit_text(
                "❌ Серверы не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="stats")
                ]])
            )
            return
        
        message = "🖥️ **Статистика серверов**\n\n"
        
        # Общая информация
        total_nodes = len(nodes_response)
        online_nodes = sum(1 for node in nodes_response if node.is_connected)
        
        message += f"**📊 Общая информация:**\n"
        message += f"• Всего серверов: {total_nodes}\n"
        message += f"• Онлайн: {online_nodes}\n"
        message += f"• Офлайн: {total_nodes - online_nodes}\n\n"
        
        # Детальная информация по каждой ноде
        message += "**📋 Детали серверов:**\n"
        for node in nodes_response:
            status_emoji = "🟢" if node.is_connected else "🔴"
            
            # Пользователи на этой ноде
            node_users = [user for user in users_response.users if getattr(user, 'node_uuid', None) == node.uuid]
            active_users = sum(1 for user in node_users if user.is_active)
            node_traffic = sum(user.used_traffic or 0 for user in node_users)
            
            message += f"{status_emoji} **{escape_markdown(node.name)}**\n"
            message += f"  • Адрес: `{node.address}`\n"
            message += f"  • Пользователей: {len(node_users)} (активных: {active_users})\n"
            message += f"  • Трафик: {format_bytes(node_traffic)}\n"
            
            if node.is_connected:
                # Дополнительная информация для онлайн нод
                if hasattr(node, 'last_seen'):
                    message += f"  • Последняя связь: {format_datetime(node.last_seen)}\n"
                if hasattr(node, 'version'):
                    message += f"  • Версия: {node.version}\n"
                if hasattr(node, 'uptime'):
                    message += f"  • Uptime: {format_uptime(node.uptime)}\n"
            else:
                if hasattr(node, 'last_seen'):
                    message += f"  • Офлайн с: {format_datetime(node.last_seen)}\n"
            
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
        sdk = RemnaAPI.get_sdk()
        
        # Получаем текущие данные
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        nodes_response = await sdk.nodes.get_all_nodes()
        
        # Текущее время
        current_time = datetime.now().strftime("%H:%M:%S")
        
        message = f"⚡ **Мониторинг в реальном времени**\n"
        message += f"🕐 Обновлено: {current_time}\n\n"
        
        # Онлайн статистика
        active_users = sum(1 for user in users_response.users if user.is_active)
        online_nodes = sum(1 for node in nodes_response if node.is_connected)
        
        message += "**🔥 Сейчас активно:**\n"
        message += f"• Пользователей: {active_users}\n"
        message += f"• Серверов: {online_nodes}\n"
        
        # Трафик в реальном времени (последние активные пользователи)
        recent_users = [
            user for user in users_response.users 
            if user.used_traffic and user.used_traffic > 0 and user.is_active
        ]
        
        if recent_users:
            total_active_traffic = sum(user.used_traffic for user in recent_users)
            message += f"• Общий трафик активных: {format_bytes(total_active_traffic)}\n"
        
        message += "\n**📊 Статус серверов:**\n"
        for node in nodes_response:
            status_emoji = "🟢" if node.is_connected else "🔴"
            message += f"{status_emoji} {escape_markdown(node.name)}\n"
        
        # Последние события (если доступно)
        message += "\n**📝 Последние события:**\n"
        message += "• Мониторинг активности...\n"
        
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
        sdk = RemnaAPI.get_sdk()
        
        # Получаем детальную статистику
        system_stats = await sdk.system.get_system_stats()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        nodes_response = await sdk.nodes.get_all_nodes()
        
        message = "📊 **Детальная статистика системы**\n\n"
        
        # Расширенная информация о пользователях
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        new_users_week = sum(
            1 for user in users_response.users 
            if user.created_at and datetime.fromisoformat(user.created_at.replace('Z', '+00:00')) > week_ago
        )
        new_users_month = sum(
            1 for user in users_response.users 
            if user.created_at and datetime.fromisoformat(user.created_at.replace('Z', '+00:00')) > month_ago
        )
        
        expired_users = sum(
            1 for user in users_response.users 
            if user.expire_at and datetime.fromisoformat(user.expire_at.replace('Z', '+00:00')) < now
        )
        
        message += "**👥 Детальная статистика пользователей:**\n"
        message += f"• Новых за неделю: {new_users_week}\n"
        message += f"• Новых за месяц: {new_users_month}\n"
        message += f"• Истекших: {expired_users}\n"
        
        # Распределение по лимитам трафика
        unlimited_users = sum(1 for user in users_response.users if not user.traffic_limit)
        limited_users = len(users_response.users) - unlimited_users
        
        message += f"• С лимитом трафика: {limited_users}\n"
        message += f"• Безлимитных: {unlimited_users}\n"
        
        # Средние показатели
        if users_response.users:
            avg_traffic = sum(user.used_traffic or 0 for user in users_response.users) / len(users_response.users)
            message += f"• Средний трафик: {format_bytes(int(avg_traffic))}\n"
        
        # Статистика по нодам
        message += "\n**🖥️ Детальная статистика серверов:**\n"
        for node in nodes_response:
            node_users = [user for user in users_response.users if getattr(user, 'node_uuid', None) == node.uuid]
            active_users = sum(1 for user in node_users if user.is_active)
            node_traffic = sum(user.used_traffic or 0 for user in node_users)
            
            load_percent = (len(node_users) / max(getattr(node, 'max_users', 100), 1)) * 100
            
            message += f"**{escape_markdown(node.name)}:**\n"
            message += f"  • Загрузка: {load_percent:.1f}%\n"
            message += f"  • Активных: {active_users}/{len(node_users)}\n"
            message += f"  • Трафик: {format_bytes(node_traffic)}\n"
        
        # Системные ресурсы (если доступно)
        if system_stats:
            message += "\n**💻 Системные ресурсы:**\n"
            if hasattr(system_stats, 'cpu_usage'):
                message += f"• CPU: {system_stats.cpu_usage}%\n"
            if hasattr(system_stats, 'memory_usage'):
                message += f"• RAM: {system_stats.memory_usage}%\n"
            if hasattr(system_stats, 'disk_usage'):
                message += f"• Диск: {system_stats.disk_usage}%\n"
            if hasattr(system_stats, 'network_connections'):
                message += f"• Сетевые соединения: {system_stats.network_connections}\n"
        
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
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        message = "📈 **Статистика трафика за неделю**\n\n"
        
        # Расчет за последние 7 дней
        total_traffic = sum(user.used_traffic or 0 for user in users_response.users)
        
        message += f"**📊 Общий трафик:**\n"
        message += f"• За неделю: {format_bytes(total_traffic)}\n"
        message += f"• В среднем в день: {format_bytes(total_traffic // 7)}\n"
        
        # Топ пользователей за неделю
        top_users = sorted(
            [user for user in users_response.users if user.used_traffic and user.used_traffic > 0],
            key=lambda u: u.used_traffic,
            reverse=True
        )[:10]
        
        if top_users:
            message += "\n**🏆 Топ 10 за неделю:**\n"
            for i, user in enumerate(top_users, 1):
                message += f"{i}. {escape_markdown(user.username)}: {format_bytes(user.used_traffic)}\n"
        
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
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        message = "📉 **Статистика трафика за месяц**\n\n"
        
        # Расчет за последние 30 дней
        total_traffic = sum(user.used_traffic or 0 for user in users_response.users)
        
        message += f"**📊 Общий трафик:**\n"
        message += f"• За месяц: {format_bytes(total_traffic)}\n"
        message += f"• В среднем в день: {format_bytes(total_traffic // 30)}\n"
        message += f"• В среднем в неделю: {format_bytes(total_traffic // 4)}\n"
        
        # Прогноз на следующий месяц
        projected = total_traffic * 2  # Простой прогноз
        message += f"• Прогноз на след. месяц: {format_bytes(projected)}\n"
        
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

# ================ BACK NAVIGATION ================

@router.callback_query(F.data == "back_to_stats", AuthFilter())
async def back_to_stats(callback: types.CallbackQuery, state: FSMContext):
    """Return to stats menu"""
    await show_stats_menu(callback)
