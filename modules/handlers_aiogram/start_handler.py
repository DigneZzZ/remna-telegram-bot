from aiogram import Router, types, F
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import logging
import os
import asyncio

from modules.handlers_aiogram.auth import AuthFilter
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import format_bytes, escape_markdown
from modules.config import (
    DASHBOARD_SHOW_SYSTEM_STATS, DASHBOARD_SHOW_SERVER_INFO,
    DASHBOARD_SHOW_USERS_COUNT, DASHBOARD_SHOW_NODES_COUNT, 
    DASHBOARD_SHOW_TRAFFIC_STATS, DASHBOARD_SHOW_UPTIME
)

logger = logging.getLogger(__name__)

router = Router()

# ================ START COMMAND ================

@router.message(Command("start"), AuthFilter())
async def start_command(message: types.Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    await show_main_menu(message)

@router.callback_query(Text("main_menu"), AuthFilter())
async def main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle main menu callback"""
    await callback.answer()
    await state.clear()
    await show_main_menu(callback.message, is_callback=True)

# ================ MAIN MENU ================

async def show_main_menu(message: types.Message, is_callback: bool = False):
    """Show main menu with system statistics"""
    
    # Строим клавиатуру
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👥 Управление пользователями", callback_data="users"))
    builder.row(types.InlineKeyboardButton(text="🖥️ Управление серверами", callback_data="nodes"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика системы", callback_data="stats"))
    builder.row(types.InlineKeyboardButton(text="🌐 Управление хостами", callback_data="hosts"))
    builder.row(types.InlineKeyboardButton(text="🔌 Управление Inbounds", callback_data="inbounds"))
    builder.row(
        types.InlineKeyboardButton(text="🔄 Массовые операции", callback_data="bulk"),
        types.InlineKeyboardButton(text="➕ Создать пользователя", callback_data="create_user")
    )
    builder.row(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))

    # Получаем статистику системы
    try:
        stats_text = await get_system_stats()
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        stats_text = "📈 **Статистика временно недоступна**"
    
    message_text = "🎛️ **Главное меню Remnawave Admin**\n\n"
    message_text += stats_text + "\n\n"
    message_text += "Выберите раздел для управления:"

    if is_callback:
        await message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            text=message_text,
            reply_markup=builder.as_markup()
        )

# ================ SYSTEM STATISTICS ================

async def get_system_stats():
    """Get system statistics based on configuration settings"""
    stats_sections = []
    
    try:
        # Системная информация (если включена)
        if DASHBOARD_SHOW_SYSTEM_STATS:
            try:
                system_stats = await get_local_system_stats()
                if system_stats:
                    stats_sections.append(system_stats)
            except Exception as e:
                logger.error(f"Error getting system stats: {e}")
        
        # Статистика пользователей (если включена)
        if DASHBOARD_SHOW_USERS_COUNT:
            try:
                user_stats = await get_user_stats()
                if user_stats:
                    stats_sections.append(user_stats)
            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
        
        # Статистика узлов (если включена)
        if DASHBOARD_SHOW_NODES_COUNT:
            try:
                node_stats = await get_node_stats()
                if node_stats:
                    stats_sections.append(node_stats)
            except Exception as e:
                logger.error(f"Error getting node stats: {e}")
        
        # Статистика трафика в реальном времени (если включена)
        if DASHBOARD_SHOW_TRAFFIC_STATS:
            try:
                traffic_stats = await get_traffic_stats()
                if traffic_stats:
                    stats_sections.append(traffic_stats)
            except Exception as e:
                logger.warning(f"Could not get realtime traffic stats: {e}")
        
        # Информация о серверах (если включена)
        if DASHBOARD_SHOW_SERVER_INFO:
            try:
                server_stats = await get_server_info()
                if server_stats:
                    stats_sections.append(server_stats)
            except Exception as e:
                logger.error(f"Error getting server stats: {e}")
        
        # Собираем все секции в одну строку
        if stats_sections:
            result = "📈 **Системная статистика**\n\n" + "\n".join(stats_sections)
        else:
            result = "📈 **Статистика**\n\nОтображение статистики отключено в настройках."
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return "📈 **Статистика временно недоступна**"

async def get_local_system_stats():
    """Get local system statistics"""
    try:
        import psutil
        
        # Определяем, запущены ли мы в Docker
        in_docker = os.path.exists('/.dockerenv')
        
        if in_docker:
            # В Docker - читаем информацию из cgroup
            try:
                cpu_cores, cpu_percent, memory = await get_docker_stats()
            except Exception as e:
                logger.warning(f"Error reading Docker cgroup stats, falling back to psutil: {e}")
                cpu_cores = psutil.cpu_count()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
        else:
            cpu_cores = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
        
        system_stats = f"🖥️ **Система**:\n"
        system_stats += f"  • CPU: {cpu_cores} ядер, {cpu_percent:.1f}%\n"
        system_stats += f"  • RAM: {format_bytes(memory.used)} / {format_bytes(memory.total)} ({memory.percent:.1f}%)\n"
        
        if DASHBOARD_SHOW_UPTIME:
            uptime_seconds = psutil.boot_time()
            current_time = datetime.now().timestamp()
            uptime = int(current_time - uptime_seconds)
            uptime_str = format_uptime(uptime)
            system_stats += f"  • Uptime: {uptime_str}\n"
        
        return system_stats
        
    except ImportError:
        logger.warning("psutil not available, skipping system stats")
        return None
    except Exception as e:
        logger.error(f"Error getting local system stats: {e}")
        return None

async def get_docker_stats():
    """Get Docker container statistics from cgroup"""
    # CPU cores
    cpu_cores = 0
    cpu_quota_file = '/sys/fs/cgroup/cpu/cpu.cfs_quota_us'
    cpu_period_file = '/sys/fs/cgroup/cpu/cpu.cfs_period_us'
    
    # Альтернативные пути для cgroup v2
    if not os.path.exists(cpu_quota_file):
        cpu_quota_file = '/sys/fs/cgroup/cpu.max'
        cpu_period_file = None
    
    if os.path.exists(cpu_quota_file):
        with open(cpu_quota_file, 'r') as f:
            content = f.read().strip()
        
        if cpu_period_file and os.path.exists(cpu_period_file):
            quota = int(content)
            with open(cpu_period_file, 'r') as f:
                period = int(f.read().strip())
            
            if quota > 0 and period > 0:
                cpu_cores = max(1, quota // period)
            else:
                import psutil
                cpu_cores = psutil.cpu_count()
        else:
            if 'max' in content:
                import psutil
                cpu_cores = psutil.cpu_count()
            else:
                parts = content.split()
                if len(parts) >= 2:
                    quota = int(parts[0])
                    period = int(parts[1])
                    if quota > 0 and period > 0:
                        cpu_cores = max(1, quota // period)
                    else:
                        import psutil
                        cpu_cores = psutil.cpu_count()
                else:
                    import psutil
                    cpu_cores = psutil.cpu_count()
    else:
        import psutil
        cpu_cores = psutil.cpu_count()
    
    # CPU usage
    import psutil
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Memory
    memory_limit_file = '/sys/fs/cgroup/memory/memory.limit_in_bytes'
    memory_usage_file = '/sys/fs/cgroup/memory/memory.usage_in_bytes'
    
    if not os.path.exists(memory_limit_file):
        memory_limit_file = '/sys/fs/cgroup/memory.max'
        memory_usage_file = '/sys/fs/cgroup/memory.current'
    
    if os.path.exists(memory_limit_file) and os.path.exists(memory_usage_file):
        with open(memory_limit_file, 'r') as f:
            limit_content = f.read().strip()
        
        with open(memory_usage_file, 'r') as f:
            memory_usage = int(f.read().strip())
        
        if limit_content == 'max':
            memory_limit = psutil.virtual_memory().total
        else:
            memory_limit = int(limit_content)
    else:
        vm = psutil.virtual_memory()
        memory_limit = vm.total
        memory_usage = vm.used
    
    class DockerMemory:
        def __init__(self, total, used):
            self.total = total
            self.used = used
            self.free = total - used
            self.percent = (used / total * 100) if total > 0 else 0
    
    memory = DockerMemory(memory_limit, memory_usage)
    
    return cpu_cores, cpu_percent, memory

async def get_user_stats():
    """Get user statistics using SDK"""
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2()
        
        if not users_response or not users_response.users:
            return None
        
        users = users_response.users
        users_count = len(users)
        active_users = sum(1 for user in users if user.is_active)
        
        # Подсчет по статусам
        user_stats = {'active': 0, 'inactive': 0, 'expired': 0}
        total_traffic = 0
        
        now = datetime.now()
        
        for user in users:
            if user.is_active:
                user_stats['active'] += 1
            else:
                user_stats['inactive'] += 1
            
            # Проверяем истекшие
            if user.expire_at:
                try:
                    expire_date = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                    if expire_date < now:
                        user_stats['expired'] += 1
                except:
                    pass
            
            if DASHBOARD_SHOW_TRAFFIC_STATS and user.used_traffic:
                total_traffic += user.used_traffic
        
        user_section = f"👥 **Пользователи** ({users_count} всего):\n"
        user_section += f"  • ✅ Активных: {user_stats['active']}\n"
        user_section += f"  • ❌ Неактивных: {user_stats['inactive']}\n"
        
        if user_stats['expired'] > 0:
            user_section += f"  • ⏰ Истекших: {user_stats['expired']}\n"
        
        if DASHBOARD_SHOW_TRAFFIC_STATS and total_traffic > 0:
            user_section += f"  • 📊 Общий трафик: {format_bytes(total_traffic)}\n"
        
        return user_section
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return None

async def get_node_stats():
    """Get node statistics using SDK"""
    try:
        sdk = RemnaAPI.get_sdk()
        nodes_response = await sdk.nodes.get_all_nodes()
        
        if not nodes_response:
            return None
        
        nodes_count = len(nodes_response)
        online_nodes = sum(1 for node in nodes_response if node.is_connected)
        
        node_section = f"�️ **Серверы**: {online_nodes}/{nodes_count} онлайн"
        
        # Дополнительная информация о нодах
        if nodes_count > 0:
            offline_nodes = nodes_count - online_nodes
            if offline_nodes > 0:
                node_section += f" (❌ {offline_nodes} офлайн)"
        
        node_section += "\n"
        
        return node_section
        
    except Exception as e:
        logger.error(f"Error getting node stats: {e}")
        return None

async def get_traffic_stats():
    """Get traffic statistics using SDK"""
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем статистику трафика через пользователей
        users_response = await sdk.users.get_all_users_v2()
        
        if not users_response or not users_response.users:
            return None
        
        # Суммируем трафик активных пользователей
        active_users = [user for user in users_response.users if user.is_active]
        
        if not active_users:
            return None
        
        total_traffic_used = sum(user.used_traffic or 0 for user in active_users)
        total_traffic_limit = sum(user.traffic_limit or 0 for user in active_users if user.traffic_limit)
        
        if total_traffic_used == 0:
            return None
        
        traffic_section = f"📊 **Активность**:\n"
        traffic_section += f"  • Использовано: {format_bytes(total_traffic_used)}\n"
        
        if total_traffic_limit > 0:
            remaining = total_traffic_limit - total_traffic_used
            usage_percent = (total_traffic_used / total_traffic_limit) * 100
            traffic_section += f"  • Осталось: {format_bytes(remaining)}\n"
            traffic_section += f"  • Использовано: {usage_percent:.1f}%\n"
        
        return traffic_section
        
    except Exception as e:
        logger.warning(f"Could not get traffic stats: {e}")
        return None

async def get_server_info():
    """Get server info using SDK"""
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем информацию о системе
        try:
            system_info = await sdk.system.get_system_info()
            if system_info:
                server_section = f"🔧 **Система**:\n"
                if hasattr(system_info, 'version'):
                    server_section += f"  • Версия: {system_info.version}\n"
                if hasattr(system_info, 'build'):
                    server_section += f"  • Сборка: {system_info.build}\n"
                return server_section
        except:
            pass
        
        # Fallback - считаем inbound'ы через ноды
        nodes_response = await sdk.nodes.get_all_nodes()
        if nodes_response:
            total_inbounds = 0
            for node in nodes_response:
                if hasattr(node, 'inbounds_count'):
                    total_inbounds += node.inbounds_count
                else:
                    # Примерная оценка
                    total_inbounds += 1 if node.is_connected else 0
            
            server_section = f"🔌 **Подключения**: {total_inbounds} активных\n"
            return server_section
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return None

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

# ================ BASIC SYSTEM STATS (FALLBACK) ================

async def get_basic_system_stats():
    """Get basic system statistics (fallback version)"""
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем статистику пользователей
        users_response = await sdk.users.get_all_users_v2()
        users_count = 0
        active_users = 0
        
        if users_response and users_response.users:
            users_count = len(users_response.users)
            active_users = sum(1 for user in users_response.users if user.is_active)

        # Получаем статистику узлов
        nodes_response = await sdk.nodes.get_all_nodes()
        nodes_count = 0
        online_nodes = 0
        
        if nodes_response:
            nodes_count = len(nodes_response)
            online_nodes = sum(1 for node in nodes_response if node.is_connected)

        # Формируем текст статистики
        stats = f"📈 **Общая статистика системы:**\n"
        stats += f"👥 Пользователи: {active_users}/{users_count}\n"
        stats += f"🖥️ Узлы: {online_nodes}/{nodes_count} онлайн\n"
        
        # Общий трафик
        if users_response and users_response.users:
            total_traffic = sum(user.used_traffic or 0 for user in users_response.users)
            if total_traffic > 0:
                stats += f"📊 Общий трафик: {format_bytes(total_traffic)}\n"
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting basic system stats: {e}")
        return "📈 **Статистика временно недоступна**"

# ================ REFRESH STATS ================

@router.callback_query(Text("refresh_stats"), AuthFilter())
async def refresh_stats(callback: types.CallbackQuery):
    """Refresh main menu statistics"""
    await callback.answer("🔄 Обновление статистики...")
    await show_main_menu(callback.message, is_callback=True)

# ================ HELP COMMAND ================

@router.message(Command("help"), AuthFilter())
async def help_command(message: types.Message):
    """Show help information"""
    help_text = """
🤖 **Remnawave Admin Bot - Справка**

**Основные команды:**
• `/start` - Главное меню
• `/help` - Эта справка

**Разделы управления:**
• 👥 **Пользователи** - Создание, редактирование, просмотр пользователей
• 🖥️ **Серверы** - Управление нодами и серверами
• 📊 **Статистика** - Мониторинг системы и трафика
• 🌐 **Хосты** - Управление доменами и хостами
• 🔌 **Inbounds** - Настройка подключений
• 🔄 **Массовые операции** - Групповые действия

**Функции пользователей:**
• Создание по шаблонам (Базовый, Премиум, Безлимитный, Пробный)
• Редактирование параметров (трафик, сроки, описание)
• Управление устройствами (HWID)
• Поиск и фильтрация

**Мониторинг:**
• Статистика в реальном времени
• Использование ресурсов системы
• Трафик по нодам и пользователям
• Уведомления о истекающих пользователях

Используйте кнопки меню для навигации по разделам.
    """
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    await message.answer(
        text=help_text,
        reply_markup=builder.as_markup()
    )

# ================ ERROR HANDLER ================

@router.callback_query(Text("error_occurred"), AuthFilter())
async def handle_error_callback(callback: types.CallbackQuery):
    """Handle error callback"""
    await callback.answer("❌ Произошла ошибка")
    await show_main_menu(callback.message, is_callback=True)

# ================ ADMIN STATUS ================

@router.message(Command("status"), AuthFilter())
async def status_command(message: types.Message):
    """Show detailed system status"""
    try:
        status_text = "🔧 **Статус системы**\n\n"
        
        # SDK статус
        try:
            sdk = RemnaAPI.get_sdk()
            status_text += "✅ **SDK**: Подключен\n"
            
            # Тест подключения к API
            users_response = await sdk.users.get_all_users_v2()
            status_text += "✅ **API**: Доступно\n"
            
            # Статистика
            users_count = len(users_response.users) if users_response and users_response.users else 0
            status_text += f"📊 **Пользователей**: {users_count}\n"
            
            nodes_response = await sdk.nodes.get_all_nodes()
            nodes_count = len(nodes_response) if nodes_response else 0
            online_nodes = sum(1 for node in nodes_response if node.is_connected) if nodes_response else 0
            status_text += f"🖥️ **Ноды**: {online_nodes}/{nodes_count}\n"
            
        except Exception as e:
            status_text += f"❌ **SDK/API**: Ошибка - {str(e)[:50]}...\n"
        
        # Системные ресурсы
        try:
            system_stats = await get_local_system_stats()
            if system_stats:
                status_text += f"\n{system_stats}"
        except Exception as e:
            status_text += f"\n❌ **Система**: {str(e)[:50]}...\n"
        
        # Время работы бота
        status_text += f"\n🕐 **Время**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_status"))
        builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        
        await message.answer(
            text=status_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.answer(
            "❌ Ошибка при получении статуса системы",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]])
        )

@router.callback_query(Text("refresh_status"), AuthFilter())
async def refresh_status(callback: types.CallbackQuery):
    """Refresh system status"""
    await callback.answer("🔄 Обновление статуса...")
    
    # Simulate the status command
    try:
        status_text = "🔧 **Статус системы**\n\n"
        
        # SDK статус
        try:
            sdk = RemnaAPI.get_sdk()
            status_text += "✅ **SDK**: Подключен\n"
            
            # Тест подключения к API
            users_response = await sdk.users.get_all_users_v2()
            status_text += "✅ **API**: Доступно\n"
            
            # Статистика
            users_count = len(users_response.users) if users_response and users_response.users else 0
            status_text += f"📊 **Пользователей**: {users_count}\n"
            
            nodes_response = await sdk.nodes.get_all_nodes()
            nodes_count = len(nodes_response) if nodes_response else 0
            online_nodes = sum(1 for node in nodes_response if node.is_connected) if nodes_response else 0
            status_text += f"🖥️ **Ноды**: {online_nodes}/{nodes_count}\n"
            
        except Exception as e:
            status_text += f"❌ **SDK/API**: Ошибка - {str(e)[:50]}...\n"
        
        # Системные ресурсы
        try:
            system_stats = await get_local_system_stats()
            if system_stats:
                status_text += f"\n{system_stats}"
        except Exception as e:
            status_text += f"\n❌ **Система**: {str(e)[:50]}...\n"
        
        # Время работы бота
        status_text += f"\n🕐 **Время**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_status"))
        builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        
        await callback.message.edit_text(
            text=status_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error refreshing status: {e}")
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)