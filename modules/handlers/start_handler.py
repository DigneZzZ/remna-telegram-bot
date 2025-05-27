import logging
import asyncio
import os
import pytz
from datetime import datetime, timezone
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.handlers.auth import AuthFilter
from modules.api.users import get_all_users
from modules.api.nodes import get_all_nodes
from modules.api.system import SystemAPI
from modules.utils.formatters_aiogram import format_bytes
from modules.config import (
    DASHBOARD_SHOW_SYSTEM_STATS, DASHBOARD_SHOW_SERVER_INFO,
    DASHBOARD_SHOW_USERS_COUNT, DASHBOARD_SHOW_NODES_COUNT, 
    DASHBOARD_SHOW_TRAFFIC_STATS, DASHBOARD_SHOW_UPTIME
)

logger = logging.getLogger(__name__)
router = Router()

# ================ DATETIME PARSING FIX ================

def parse_expiry_date_safe(expire_at_str):
    """Безопасный парсинг даты истечения с поддержкой часовых поясов"""
    if not expire_at_str:
        return None
    
    try:
        # Удаляем миллисекунды если есть
        if '.' in expire_at_str and expire_at_str.endswith('Z'):
            expire_at_str = expire_at_str.split('.')[0] + 'Z'
        
        # Парсим дату с timezone
        if expire_at_str.endswith('Z'):
            # UTC timezone
            expire_date = datetime.fromisoformat(expire_at_str.replace('Z', '+00:00'))
        elif '+' in expire_at_str or expire_at_str.count('-') > 2:
            # Уже содержит timezone
            expire_date = datetime.fromisoformat(expire_at_str)
        else:
            # Нет timezone, считаем UTC
            expire_date = datetime.fromisoformat(expire_at_str).replace(tzinfo=timezone.utc)
        
        # Приводим к UTC для сравнения
        if expire_date.tzinfo is None:
            expire_date = expire_date.replace(tzinfo=timezone.utc)
        elif expire_date.tzinfo != timezone.utc:
            expire_date = expire_date.astimezone(timezone.utc)
        
        return expire_date
        
    except Exception as e:
        logger.debug(f"Error parsing expiry date {expire_at_str}: {e}")
        return None

def get_current_utc_time():
    """Получить текущее время в UTC"""
    return datetime.now(timezone.utc)

# ================ MARKDOWN ESCAPING FIX ================

def safe_escape_markdown(text):
    """Безопасное экранирование для Markdown"""
    if not text:
        return ""
    
    text = str(text)
    
    # Заменяем проблематичные символы для MarkdownV2
    replacements = {
        '_': '\\_',
        '*': '\\*',
        '[': '\\[',
        ']': '\\]',
        '(': '\\(',
        ')': '\\)',
        '~': '\\~',
        '`': '\\`',
        '>': '\\>',
        '#': '\\#',
        '+': '\\+',
        '-': '\\-',
        '=': '\\=',
        '|': '\\|',
        '{': '\\{',
        '}': '\\}',
        '.': '\\.',
        '!': '\\!'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def escape_markdown(text):
    """Алиас для совместимости"""
    return safe_escape_markdown(text)

# ================ UTILITY FUNCTIONS ================

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

# ================ DOCKER STATS ================

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
            import psutil
            memory_limit = psutil.virtual_memory().total
        else:
            memory_limit = int(limit_content)
    else:
        import psutil
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

# ================ STATISTICS FUNCTIONS ================

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

async def get_user_stats():
    """Get user statistics with fixed date parsing"""
    try:
        users_data = await get_all_users()
        
        if not users_data:
            return None
        
        users_count = len(users_data)
        user_stats = {'active': 0, 'inactive': 0, 'expired': 0, 'disabled': 0}
        total_traffic = 0
        
        now_utc = get_current_utc_time()
        
        for user in users_data:
            status = user.get('status', '').upper()
            is_disabled = user.get('isDisabled', False)
            
            # Проверяем сначала disabled статус
            if is_disabled:
                user_stats['disabled'] += 1
                continue
            
            # Проверяем истекшие с исправленным парсингом дат
            expire_at = user.get('expireAt')
            is_expired = False
            if expire_at:
                expire_date = parse_expiry_date_safe(expire_at)
                if expire_date and expire_date < now_utc:
                    is_expired = True
                    user_stats['expired'] += 1
                    continue
            
            # Проверяем лимит трафика
            traffic_limit = user.get('trafficLimit', 0)
            used_traffic = user.get('usedTraffic', 0)
            traffic_exceeded = False
            
            if traffic_limit and traffic_limit > 0:
                if used_traffic >= traffic_limit:
                    traffic_exceeded = True
            
            # Определяем финальный статус
            if status == 'ACTIVE' and not is_expired and not traffic_exceeded:
                user_stats['active'] += 1
            else:
                user_stats['inactive'] += 1
            
            if DASHBOARD_SHOW_TRAFFIC_STATS:
                if used_traffic:
                    total_traffic += used_traffic
        
        user_section = f"👥 **Пользователи** ({users_count} всего):\n"
        user_section += f"  • ✅ Активных: {user_stats['active']}\n"
        user_section += f"  • ❌ Неактивных: {user_stats['inactive']}\n"
        
        if user_stats['expired'] > 0:
            user_section += f"  • ⏰ Истекших: {user_stats['expired']}\n"
        
        if user_stats['disabled'] > 0:
            user_section += f"  • 🚫 Отключенных: {user_stats['disabled']}\n"
        
        if DASHBOARD_SHOW_TRAFFIC_STATS and total_traffic > 0:
            user_section += f"  • 📊 Общий трафик: {format_bytes(total_traffic)}\n"
        
        return user_section
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return None

async def get_node_stats():
    """Get node statistics using direct HTTP API"""
    try:
        nodes_data = await get_all_nodes()
        
        if not nodes_data:
            return None
        
        nodes_count = len(nodes_data)
        
        # Правильный подсчет статусов нод согласно API v1.6.5
        online_nodes = 0
        disabled_nodes = 0
        
        for node in nodes_data:
            is_disabled = node.get('isDisabled', False)
            is_connected = node.get('isConnected', False)
            
            if is_disabled:
                disabled_nodes += 1
            elif is_connected:
                online_nodes += 1
        
        offline_nodes = nodes_count - online_nodes - disabled_nodes
        
        node_section = f"🖥️ **Серверы**: {online_nodes}/{nodes_count} онлайн"
        
        # Дополнительная информация о нодах
        if offline_nodes > 0:
            node_section += f" (❌ {offline_nodes} офлайн)"
        
        if disabled_nodes > 0:
            node_section += f" (🚫 {disabled_nodes} отключено)"
        
        node_section += "\n"
        
        return node_section
        
    except Exception as e:
        logger.error(f"Error getting node stats: {e}")
        return None

async def get_traffic_stats():
    """Get traffic statistics using direct HTTP API"""
    try:
        users_data = await get_all_users()
        
        if not users_data:
            return None
        
        # Суммируем трафик активных пользователей
        active_users = [user for user in users_data if user.get('status') == 'ACTIVE']
        
        if not active_users:
            return None
        
        total_traffic_used = sum(user.get('usedTraffic', 0) or 0 for user in active_users)
        total_traffic_limit = sum(user.get('trafficLimit', 0) or 0 for user in active_users if user.get('trafficLimit'))
        
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
    """Get server info using direct HTTP API"""
    try:
        # Получаем информацию о системе через SystemAPI
        system_stats = await SystemAPI.get_stats()
        
        if system_stats:
            server_section = f"🔧 **Система**:\n"
            
            if system_stats.get('version'):
                server_section += f"  • Версия: {safe_escape_markdown(system_stats.get('version'))}\n"
            
            if system_stats.get('uptime'):
                uptime_str = format_uptime(system_stats.get('uptime'))
                server_section += f"  • Uptime: {uptime_str}\n"
            
            if system_stats.get('connectionsCount'):
                server_section += f"  • Подключений: {system_stats.get('connectionsCount')}\n"
            
            return server_section
        
        # Fallback - получаем информацию через inbound'ы
        try:
            from modules.api.inbounds import get_all_inbounds
            inbounds_data = await get_all_inbounds()
            
            if inbounds_data:
                active_inbounds = sum(1 for inbound in inbounds_data if inbound.get('isEnabled', True))
                server_section = f"🔌 **Inbounds**: {active_inbounds}/{len(inbounds_data)} активных\n"
                return server_section
        except Exception as e:
            logger.warning(f"Could not get inbounds info: {e}")
        
        # Альтернативный fallback - считаем активные ноды
        nodes_data = await get_all_nodes()
        if nodes_data:
            active_nodes = sum(1 for node in nodes_data 
                if node.get('isConnected', False) and not node.get('isDisabled', False))
            server_section = f"🔌 **Активные ноды**: {active_nodes}\n"
            return server_section
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return None

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

# ================ MAIN MENU ================

async def show_main_menu(message: types.Message, is_callback: bool = False):
    """Show main menu with fixed statistics"""
    try:
        # Получаем статистику системы
        stats_text = await get_system_stats()
        
        # Формируем основное сообщение
        message_text = "🎛️ **Главное меню Remnawave Admin**\n\n"
        message_text += stats_text + "\n\n"
        message_text += "Выберите раздел для управления:"
        
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
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_main_menu"))

        # Отправляем или редактируем сообщение
        try:
            if is_callback:
                await message.edit_text(
                    text=message_text,
                    reply_markup=builder.as_markup(),
                    parse_mode="MarkdownV2"
                )
            else:
                await message.answer(
                    text=message_text,
                    reply_markup=builder.as_markup(),
                    parse_mode="MarkdownV2"
                )
        except Exception as parse_error:
            logger.warning(f"Markdown parsing failed, using fallback: {parse_error}")
            # Fallback без форматирования
            fallback_text = "🎛️ Главное меню Remnawave Admin\n\nВыберите раздел для управления:"
            
            if is_callback:
                await message.edit_text(
                    text=fallback_text,
                    reply_markup=builder.as_markup()
                )
            else:
                await message.answer(
                    text=fallback_text,
                    reply_markup=builder.as_markup()
                )
            
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        
        # Emergency fallback
        fallback_text = "🎛️ Главное меню Remnawave Admin\n\nВыберите раздел для управления:"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="👥 Пользователи", callback_data="users"))
        builder.row(types.InlineKeyboardButton(text="🖥️ Ноды", callback_data="nodes"))
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_main_menu"))
        
        if is_callback:
            await message.edit_text(
                text=fallback_text,
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer(
                text=fallback_text,
                reply_markup=builder.as_markup()
            )

# ================ COMMANDS ================

@router.message(Command("start"), AuthFilter())
async def start_command(message: types.Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    await show_main_menu(message)

@router.message(Command("menu"), AuthFilter())
async def menu_command(message: types.Message, state: FSMContext):
    """Handle /menu command"""
    await state.clear()
    await show_main_menu(message)

@router.message(Command("status"), AuthFilter())
async def status_command(message: types.Message):
    """Show detailed system status with fixed date parsing"""
    try:
        status_text = "🔧 **Статус системы**\n\n"
        
        # API статус
        try:
            users_data = await get_all_users()
            status_text += "✅ **API**: Доступно\n"
            
            # Статистика пользователей с исправленным парсингом дат
            users_count = len(users_data) if users_data else 0
            if users_data:
                active_users = 0
                now_utc = get_current_utc_time()
                
                for user in users_data:
                    status = user.get('status', '').upper()
                    is_disabled = user.get('isDisabled', False)
                    
                    if is_disabled:
                        continue
                    
                    # Проверяем истечение с исправленным парсингом
                    expire_at = user.get('expireAt')
                    is_expired = False
                    if expire_at:
                        expire_date = parse_expiry_date_safe(expire_at)
                        if expire_date and expire_date < now_utc:
                            is_expired = True
                    
                    # Проверяем лимит трафика
                    traffic_limit = user.get('trafficLimit', 0)
                    used_traffic = user.get('usedTraffic', 0)
                    traffic_exceeded = False
                    
                    if traffic_limit and traffic_limit > 0:
                        if used_traffic >= traffic_limit:
                            traffic_exceeded = True
                    
                    if status == 'ACTIVE' and not is_expired and not traffic_exceeded:
                        active_users += 1
                
                status_text += f"📊 **Пользователей**: {active_users}/{users_count}\n"
            else:
                status_text += f"📊 **Пользователей**: 0\n"
            
            # Статистика нод
            nodes_data = await get_all_nodes()
            if nodes_data:
                nodes_count = len(nodes_data)
                online_nodes = sum(1 for node in nodes_data 
                                 if node.get('isConnected', False) and not node.get('isDisabled', False))
                status_text += f"🖥️ **Ноды**: {online_nodes}/{nodes_count}\n"
            else:
                status_text += f"🖥️ **Ноды**: 0/0\n"
            
        except Exception as e:
            status_text += f"❌ **API**: Ошибка \\- {safe_escape_markdown(str(e)[:50])}\n"
        
        # Системная статистика
        try:
            system_stats = await SystemAPI.get_stats()
            if system_stats:
                status_text += "\n🔧 **Статистика системы**:\n"
                if system_stats.get('version'):
                    status_text += f"• Версия: {safe_escape_markdown(system_stats.get('version'))}\n"
                if system_stats.get('uptime'):
                    uptime_str = format_uptime(system_stats.get('uptime'))
                    status_text += f"• Uptime: {safe_escape_markdown(uptime_str)}\n"
                if system_stats.get('memoryUsage'):
                    status_text += f"• Память: {system_stats.get('memoryUsage')}%\n"
                if system_stats.get('cpuUsage'):
                    status_text += f"• CPU: {system_stats.get('cpuUsage')}%\n"
        except Exception as e:
            status_text += f"\n❌ **Система**: {safe_escape_markdown(str(e)[:50])}\n"
        
        # Системные ресурсы (локальные)
        try:
            local_stats = await get_local_system_stats()
            if local_stats:
                status_text += f"\n{local_stats}"
        except Exception as e:
            status_text += f"\n❌ **Локальная система**: {safe_escape_markdown(str(e)[:50])}\n"
        
        # Время работы бота
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status_text += f"\n🕐 **Время**: {safe_escape_markdown(current_time)}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_status"))
        builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        
        try:
            await message.answer(
                text=status_text,
                reply_markup=builder.as_markup(),
                parse_mode="MarkdownV2"
            )
        except Exception as parse_error:
            # Fallback без форматирования
            await message.answer(
                "❌ Ошибка при получении статуса системы",
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

@router.message(Command("help"), AuthFilter())
async def help_command(message: types.Message):
    """Show help information"""
    help_text = """
🤖 **Remnawave Admin Bot - Справка**

**Основные команды:**
• `/start` - Главное меню
• `/help` - Эта справка
• `/status` - Статус системы

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

Используйте кнопки меню для навигации по разделам\\.
    """
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    await message.answer(
        text=help_text,
        reply_markup=builder.as_markup()
    )

# ================ CALLBACK HANDLERS ================

@router.callback_query(F.data == "main_menu", AuthFilter())
async def main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle main menu callback"""
    await callback.answer()
    await state.clear()
    await show_main_menu(callback.message, is_callback=True)

@router.callback_query(F.data == "refresh_main_menu", AuthFilter())
async def refresh_main_menu(callback: types.CallbackQuery):
    """Refresh main menu with proper error handling"""
    await callback.answer("🔄 Обновление...")
    
    try:
        await show_main_menu(callback.message, is_callback=True)
        
    except Exception as e:
        logger.error(f"Error refreshing main menu: {e}")
        await callback.answer("❌ Ошибка при обновлении", show_alert=True)

@router.callback_query(F.data == "refresh_status", AuthFilter())
async def refresh_status(callback: types.CallbackQuery):
    """Refresh system status with proper error handling"""
    await callback.answer("🔄 Обновление статуса...")
    
    try:
        # Создаем псевдо-сообщение для вызова status_command
        await status_command(callback.message)
        
    except Exception as e:
        logger.error(f"Error refreshing status: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при обновлении статуса",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]])
        )

@router.callback_query(F.data == "refresh_stats", AuthFilter())
async def refresh_stats(callback: types.CallbackQuery):
    """Refresh main menu statistics"""
    await callback.answer("🔄 Обновление статистики...")
    await show_main_menu(callback.message, is_callback=True)

@router.callback_query(F.data == "error_occurred", AuthFilter())
async def handle_error_callback(callback: types.CallbackQuery):
    """Handle error callback"""
    await callback.answer("❌ Произошла ошибка")
    await show_main_menu(callback.message, is_callback=True)

logger.info("Start handlers module loaded successfully with datetime and markdown fixes")