"""
Утилиты для форматирования данных в Aiogram боте
"""
import datetime
from typing import Dict, Any, List

def format_bytes(bytes_value: int) -> str:
    """Форматировать байты в человекочитаемый формат"""
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = abs(bytes_value)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def format_duration(seconds: int) -> str:
    """Форматировать длительность в человекочитаемый формат"""
    if seconds <= 0:
        return "0 сек"
    
    units = [
        ("дн", 86400),
        ("ч", 3600),
        ("мин", 60),
        ("сек", 1)
    ]
    
    result = []
    for name, unit_seconds in units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            seconds %= unit_seconds
            result.append(f"{count} {name}")
    
    return " ".join(result[:2])  # Показываем только 2 самые большие единицы

def format_datetime(dt_string: str) -> str:
    """Форматировать дату и время"""
    try:
        if isinstance(dt_string, str):
            # Попробуем разные форматы
            for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt = datetime.datetime.strptime(dt_string, fmt)
                    break
                except ValueError:
                    continue
            else:
                return dt_string  # Если не удалось распарсить
        else:
            dt = dt_string
        
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return str(dt_string)

def format_user_details(user: Dict[str, Any]) -> str:
    """Форматировать детали пользователя"""
    message = f"👤 **Пользователь: {user.get('username', 'N/A')}**\n\n"
    
    # Основная информация
    message += f"🆔 UUID: `{user.get('uuid', 'N/A')}`\n"
    message += f"📧 Email: `{user.get('email', 'N/A')}`\n"
    message += f"🏷️ Имя: `{user.get('username', 'N/A')}`\n"
    
    # Статус
    is_active = user.get('isActive', False)
    status_emoji = "✅" if is_active else "❌"
    message += f"{status_emoji} Статус: {'Активен' if is_active else 'Неактивен'}\n"
    
    # Даты
    if user.get('createdAt'):
        message += f"📅 Создан: {format_datetime(user['createdAt'])}\n"
    
    if user.get('expiryTime'):
        message += f"⏰ Истекает: {format_datetime(user['expiryTime'])}\n"
    
    # Трафик
    if 'usedTrafficBytes' in user:
        used_traffic = user['usedTrafficBytes']
        traffic_limit = user.get('trafficLimitBytes', 0)
        
        message += f"\n📊 **Трафик:**\n"
        message += f"📈 Использовано: {format_bytes(used_traffic)}\n"
        
        if traffic_limit > 0:
            message += f"📊 Лимит: {format_bytes(traffic_limit)}\n"
            percentage = (used_traffic / traffic_limit) * 100 if traffic_limit > 0 else 0
            message += f"📋 Использовано: {percentage:.1f}%\n"
        else:
            message += f"📊 Лимит: Безлимитный\n"
    
    # Подключения
    if 'connectionsCount' in user:
        message += f"🔗 Подключений: {user['connectionsCount']}\n"
    
    # Inbound'ы
    if user.get('inbounds'):
        inbounds_count = len(user['inbounds'])
        message += f"📡 Inbound'ов: {inbounds_count}\n"
    
    return message

def format_node_details(node: Dict[str, Any]) -> str:
    """Форматировать детали ноды"""
    message = f"🖥️ **Сервер: {node.get('name', 'N/A')}**\n\n"
    
    # Основная информация
    message += f"🆔 UUID: `{node.get('uuid', 'N/A')}`\n"
    message += f"🌐 Адрес: `{node.get('address', 'N/A')}`\n"
    message += f"🔌 Порт: `{node.get('port', 'N/A')}`\n"
    message += f"🌍 Страна: `{node.get('countryCode', 'N/A')}`\n"
    
    # Статус
    is_disabled = node.get('isDisabled', True)
    is_connected = node.get('isConnected', False)
    
    if is_disabled:
        status = "❌ Отключен"
    elif is_connected:
        status = "✅ Онлайн"
    else:
        status = "⚠️ Оффлайн"
    
    message += f"📶 Статус: {status}\n"
    
    # Трафик и настройки
    multiplier = node.get('consumptionMultiplier', 1.0)
    message += f"📊 Множитель: `{multiplier}x`\n"
    
    traffic_limit = node.get('trafficLimitBytes', 0)
    if traffic_limit > 0:
        message += f"📈 Лимит трафика: {format_bytes(traffic_limit)}\n"
    else:
        message += f"📈 Лимит трафика: Безлимитный\n"
    
    # Даты
    if node.get('createdAt'):
        message += f"📅 Создан: {format_datetime(node['createdAt'])}\n"
    
    if node.get('lastConnected'):
        message += f"🔗 Последнее подключение: {format_datetime(node['lastConnected'])}\n"
    
    # Пользователи
    if 'usersCount' in node:
        message += f"👥 Пользователей: {node['usersCount']}\n"
    
    return message

def format_inbound_details(inbound: Dict[str, Any]) -> str:
    """Форматировать детали inbound"""
    message = f"📡 **Inbound: {inbound.get('tag', 'N/A')}**\n\n"
    
    # Основная информация
    message += f"🆔 UUID: `{inbound.get('uuid', 'N/A')}`\n"
    message += f"🏷️ Тег: `{inbound.get('tag', 'N/A')}`\n"
    message += f"🔧 Протокол: `{inbound.get('type', 'N/A')}`\n"
    message += f"🔌 Порт: `{inbound.get('port', 'N/A')}`\n"
    
    # Настройки
    if inbound.get('settings'):
        settings = inbound['settings']
        if isinstance(settings, dict):
            for key, value in settings.items():
                if key not in ['clients', 'fallbacks']:
                    message += f"⚙️ {key}: `{value}`\n"
    
    # Статистика
    if 'users' in inbound:
        users_stats = inbound['users']
        enabled_users = users_stats.get('enabled', 0)
        disabled_users = users_stats.get('disabled', 0)
        total_users = enabled_users + disabled_users
        message += f"👥 Пользователи: {enabled_users}/{total_users} активных\n"
    
    if 'nodes' in inbound:
        nodes_stats = inbound['nodes']
        enabled_nodes = nodes_stats.get('enabled', 0)
        disabled_nodes = nodes_stats.get('disabled', 0)
        total_nodes = enabled_nodes + disabled_nodes
        message += f"🖥️ Серверы: {enabled_nodes}/{total_nodes} активных\n"
    
    # Даты
    if inbound.get('createdAt'):
        message += f"📅 Создан: {format_datetime(inbound['createdAt'])}\n"
    
    return message

def format_host_details(host: Dict[str, Any]) -> str:
    """Форматировать детали хоста"""
    message = f"🌐 **Хост: {host.get('remark', 'N/A')}**\n\n"
    
    # Основная информация
    message += f"🆔 UUID: `{host.get('uuid', 'N/A')}`\n"
    message += f"📝 Описание: `{host.get('remark', 'N/A')}`\n"
    message += f"🌐 Адрес: `{host.get('address', 'N/A')}`\n"
    message += f"🔌 Порт: `{host.get('port', 'N/A')}`\n"
    
    # TLS настройки
    if host.get('sni'):
        message += f"🔒 SNI: `{host['sni']}`\n"
    
    if host.get('host'):
        message += f"🏠 Host: `{host['host']}`\n"
    
    if host.get('path'):
        message += f"🛣️ Путь: `{host['path']}`\n"
    
    # Дополнительные настройки
    if host.get('alpn'):
        message += f"🔄 ALPN: `{host['alpn']}`\n"
    
    if host.get('fingerprint'):
        message += f"👆 Fingerprint: `{host['fingerprint']}`\n"
    
    allow_insecure = host.get('allowInsecure', False)
    message += f"🔐 Allow Insecure: {'Да' if allow_insecure else 'Нет'}\n"
    
    # Inbound
    if host.get('inbound'):
        inbound = host['inbound']
        if isinstance(inbound, dict):
            message += f"📡 Inbound: `{inbound.get('tag', 'N/A')}`\n"
    
    return message

def format_system_stats(stats: Dict[str, Any]) -> str:
    """Форматировать системную статистику"""
    message = "📊 **Системная статистика**\n\n"
    
    # Пользователи
    if 'users' in stats:
        users = stats['users']
        message += f"👥 **Пользователи:**\n"
        message += f"   • Всего: {users.get('total', 0)}\n"
        message += f"   • Активных: {users.get('active', 0)}\n"
        message += f"   • Онлайн: {users.get('online', 0)}\n\n"
    
    # Серверы
    if 'nodes' in stats:
        nodes = stats['nodes']
        message += f"🖥️ **Серверы:**\n"
        message += f"   • Всего: {nodes.get('total', 0)}\n"
        message += f"   • Онлайн: {nodes.get('online', 0)}\n"
        message += f"   • Офлайн: {nodes.get('offline', 0)}\n\n"
    
    # Трафик
    if 'traffic' in stats:
        traffic = stats['traffic']
        message += f"📈 **Трафик:**\n"
        message += f"   • Сегодня: {format_bytes(traffic.get('today', 0))}\n"
        message += f"   • Этот месяц: {format_bytes(traffic.get('thisMonth', 0))}\n"
        message += f"   • Всего: {format_bytes(traffic.get('total', 0))}\n\n"
    
    # Система
    if 'system' in stats:
        system = stats['system']
        message += f"💻 **Система:**\n"
        if 'cpu' in system:
            message += f"   • CPU: {system['cpu']:.1f}%\n"
        if 'memory' in system:
            memory = system['memory']
            used = memory.get('used', 0)
            total = memory.get('total', 1)
            percentage = (used / total) * 100 if total > 0 else 0
            message += f"   • Память: {format_bytes(used)}/{format_bytes(total)} ({percentage:.1f}%)\n"
        if 'disk' in system:
            disk = system['disk']
            used = disk.get('used', 0)
            total = disk.get('total', 1)
            percentage = (used / total) * 100 if total > 0 else 0
            message += f"   • Диск: {format_bytes(used)}/{format_bytes(total)} ({percentage:.1f}%)\n"
    
    return message

def truncate_text(text: str, max_length: int = 4000) -> str:
    """Обрезать текст до максимальной длины для Telegram"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def escape_markdown(text: str) -> str:
    """Экранировать специальные символы для Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
