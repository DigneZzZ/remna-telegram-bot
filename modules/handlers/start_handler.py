from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from modules.config import MAIN_MENU
from modules.utils.auth import check_admin
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.api.inbounds import InboundAPI
import logging

logger = logging.getLogger(__name__)

@check_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu with system statistics"""
    keyboard = [
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="users")],
        [InlineKeyboardButton("🖥️ Управление серверами", callback_data="nodes")],
        [InlineKeyboardButton("📊 Статистика системы", callback_data="stats")],
        [InlineKeyboardButton("🌐 Управление хостами", callback_data="hosts")],
        [InlineKeyboardButton("🔌 Управление Inbounds", callback_data="inbounds")],
        [InlineKeyboardButton("🔄 Массовые операции", callback_data="bulk")],
        [InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем статистику системы
    stats_text = await get_system_stats()
    
    message = "🎛️ *Главное меню Remnawave Admin*\n\n"
    message += stats_text + "\n"
    message += "Выберите раздел для управления:"

    if update.callback_query:
        await update.callback_query.answer()
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

async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        import psutil
        import os
        from datetime import datetime, timedelta

        # Определяем, запущены ли мы в Docker
        in_docker = os.path.exists('/.dockerenv')
        
        # Получаем системную информацию
        if in_docker:
            # В Docker - читаем информацию из cgroup
            try:
                # CPU cores
                cpu_cores = 0
                with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
                    quota = int(f.read().strip())
                with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us', 'r') as f:
                    period = int(f.read().strip())
                
                if quota > 0 and period > 0:
                    cpu_cores = max(1, quota // period)
                else:
                    # Если не удалось определить из cgroups, используем psutil
                    cpu_cores = psutil.cpu_count()
                
                cpu_physical_cores = cpu_cores  # В Docker это одно и то же
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Memory
                memory_limit = 0
                with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                    memory_limit = int(f.read().strip())
                
                memory_usage = 0
                with open('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r') as f:
                    memory_usage = int(f.read().strip())
                
                # Создаем объект, подобный возвращаемому psutil
                class DockerMemory:
                    def __init__(self, total, used):
                        self.total = total
                        self.used = used
                        self.free = total - used
                        self.percent = (used / total * 100) if total > 0 else 0
                
                memory = DockerMemory(memory_limit, memory_usage)
            except Exception as e:
                # Если произошла ошибка при чтении cgroup, используем psutil
                logger.error(f"Error reading Docker cgroup stats: {e}")
                cpu_cores = psutil.cpu_count()
                cpu_physical_cores = psutil.cpu_count(logical=False)
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
        else:
            # Обычная система - используем psutil
            cpu_cores = psutil.cpu_count()
            cpu_physical_cores = psutil.cpu_count(logical=False)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
        
        # Получаем uptime
        uptime_seconds = psutil.boot_time()
        current_time = datetime.now().timestamp()
        uptime = int(current_time - uptime_seconds)
        
        # Форматируем время работы
        uptime_days = uptime // (24 * 3600)
        uptime_hours = (uptime % (24 * 3600)) // 3600
        uptime_minutes = (uptime % 3600) // 60
        
        # Получаем статистику пользователей
        users_response = await UserAPI.get_all_users()
        users_count = 0
        user_stats = {
            'ACTIVE': 0,
            'DISABLED': 0,
            'LIMITED': 0,
            'EXPIRED': 0
        }
        total_traffic = 0
        
        if users_response:
            # Проверяем разные возможные структуры ответа
            users = []
            if isinstance(users_response, dict):
                if 'users' in users_response:
                    users = users_response['users']
                elif 'response' in users_response and 'users' in users_response['response']:
                    users = users_response['response']['users']
            elif isinstance(users_response, list):
                users = users_response
            
            users_count = len(users)
            
            # Подсчитываем статистику по статусам
            for user in users:
                status = user.get('status', 'UNKNOWN')
                if status in user_stats:
                    user_stats[status] += 1
                
                # Суммируем трафик
                traffic_bytes = user.get('usedTrafficBytes', 0)
                if isinstance(traffic_bytes, (int, float)):
                    total_traffic += traffic_bytes
                elif isinstance(traffic_bytes, str) and traffic_bytes.isdigit():
                    total_traffic += int(traffic_bytes)

        # Получаем статистику узлов
        nodes_response = await NodeAPI.get_all_nodes()
        nodes_count = 0
        online_nodes = 0
        if nodes_response:
            # Проверяем разные возможные структуры ответа
            nodes = []
            if isinstance(nodes_response, dict):
                if 'nodes' in nodes_response:
                    nodes = nodes_response['nodes']
                elif 'response' in nodes_response and 'nodes' in nodes_response['response']:
                    nodes = nodes_response['response']['nodes']
            elif isinstance(nodes_response, list):
                nodes = nodes_response
            
            nodes_count = len(nodes)
            online_nodes = sum(1 for node in nodes if node.get('isConnected'))

        # Получаем статистику inbound'ов
        inbounds_response = await InboundAPI.get_inbounds()
        inbounds_count = 0
        if inbounds_response:
            # Проверяем разные возможные структуры ответа
            inbounds = []
            if isinstance(inbounds_response, dict):
                if 'inbounds' in inbounds_response:
                    inbounds = inbounds_response['inbounds']
                elif 'response' in inbounds_response and 'inbounds' in inbounds_response['response']:
                    inbounds = inbounds_response['response']['inbounds']
            elif isinstance(inbounds_response, list):
                inbounds = inbounds_response
            
            inbounds_count = len(inbounds)

        # Функция для форматирования байтов
        def format_bytes(bytes_value):
            if not bytes_value:
                return "0 B"
            
            if isinstance(bytes_value, str):
                try:
                    bytes_value = float(bytes_value)
                except (ValueError, TypeError):
                    return bytes_value
                    
            if bytes_value == 0:
                return "0 B"

            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.2f} PB"

        # Формируем детальную статистику
        stats = f"📈 *Системная статистика*\n\n"
        
        # Системные ресурсы
        stats += f"🖥️ *Система*:\n"
        stats += f"  • CPU: {cpu_cores} ядер ({cpu_physical_cores} физ.), {cpu_percent}%\n"
        stats += f"  • RAM: {format_bytes(memory.used)} / {format_bytes(memory.total)} ({memory.percent:.1f}%)\n"
        stats += f"  • Uptime: {uptime_days}д {uptime_hours}ч {uptime_minutes}м\n\n"
        
        # Статистика пользователей
        stats += f"👥 *Пользователи* ({users_count} всего):\n"
        for status, count in user_stats.items():
            if count > 0:
                emoji = {"ACTIVE": "✅", "DISABLED": "❌", "LIMITED": "⚠️", "EXPIRED": "⏰"}.get(status, "❓")
                stats += f"  • {emoji} {status}: {count}\n"
        
        if total_traffic > 0:
            stats += f"  • Общий трафик: {format_bytes(total_traffic)}\n"
        
        stats += f"\n🖥️ *Серверы*: {online_nodes}/{nodes_count} онлайн\n"
        stats += f"🔌 *Inbound'ы*: {inbounds_count} шт.\n"
        
        return stats
        
    except ImportError:
        # Если psutil не установлен, используем базовую версию
        logger.warning("psutil not available, using basic stats")
        return await get_basic_system_stats()
        
    except Exception as e:
        logger.error(f"Error getting comprehensive system stats: {e}")
        return await get_basic_system_stats()


async def get_basic_system_stats():
    """Get basic system statistics (fallback version)"""
    try:
        # Получаем статистику пользователей
        users_response = await UserAPI.get_all_users()
        users_count = 0
        active_users = 0
        if users_response:
            # Проверяем разные возможные структуры ответа
            users = []
            if isinstance(users_response, dict):
                if 'users' in users_response:
                    users = users_response['users']
                elif 'response' in users_response and 'users' in users_response['response']:
                    users = users_response['response']['users']
            elif isinstance(users_response, list):
                users = users_response
            
            users_count = len(users)
            active_users = sum(1 for user in users if user.get('status') == 'ACTIVE')

        # Получаем статистику узлов
        nodes_response = await NodeAPI.get_all_nodes()
        nodes_count = 0
        online_nodes = 0
        if nodes_response:
            # Проверяем разные возможные структуры ответа
            nodes = []
            if isinstance(nodes_response, dict):
                if 'nodes' in nodes_response:
                    nodes = nodes_response['nodes']
                elif 'response' in nodes_response and 'nodes' in nodes_response['response']:
                    nodes = nodes_response['response']['nodes']
            elif isinstance(nodes_response, list):
                nodes = nodes_response
            
            nodes_count = len(nodes)
            online_nodes = sum(1 for node in nodes if node.get('isConnected'))

        # Получаем статистику inbound'ов
        inbounds_response = await InboundAPI.get_inbounds()
        inbounds_count = 0
        if inbounds_response:
            # Проверяем разные возможные структуры ответа
            inbounds = []
            if isinstance(inbounds_response, dict):
                if 'inbounds' in inbounds_response:
                    inbounds = inbounds_response['inbounds']
                elif 'response' in inbounds_response and 'inbounds' in inbounds_response['response']:
                    inbounds = inbounds_response['response']['inbounds']
            elif isinstance(inbounds_response, list):
                inbounds = inbounds_response
            
            inbounds_count = len(inbounds)

        # Формируем текст статистики
        stats = f"📈 *Общая статистика системы:*\n"
        stats += f"👥 Пользователи: {active_users}/{users_count}\n"
        stats += f"🖥️ Узлы: {online_nodes}/{nodes_count} онлайн\n"
        stats += f"🔌 Inbound'ы: {inbounds_count} шт.\n"
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting basic system stats: {e}")
        return "📈 *Статистика временно недоступна*\n"
