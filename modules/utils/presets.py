"""
Модуль с пресетами (шаблонами) настроек для создания пользователей.
Каждый пресет содержит полный набор конфигураций для создания пользователя.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Пресеты для лимитов трафика (в байтах)
TRAFFIC_LIMIT_PRESETS = {
    "50 ГБ": 50 * 1024 * 1024 * 1024,
    "100 ГБ": 100 * 1024 * 1024 * 1024,
    "200 ГБ": 200 * 1024 * 1024 * 1024,
    "400 ГБ": 400 * 1024 * 1024 * 1024,
    "600 ГБ": 600 * 1024 * 1024 * 1024,
    "800 ГБ": 800 * 1024 * 1024 * 1024,
    "1 ТБ": 1024 * 1024 * 1024 * 1024,
    "2 ТБ": 2 * 1024 * 1024 * 1024 * 1024,
    "5 ТБ": 5 * 1024 * 1024 * 1024 * 1024,
    "Безлимитный": 0
}

# Пресеты для лимита устройств
DEVICE_LIMIT_PRESETS = {
    "1 устройство": 1,
    "2 устройства": 2,
    "3 устройства": 3,
    "4 устройства": 4,
    "5 устройств": 5,
    "10 устройств": 10,
    "Без лимита": 0
}

# Пресеты для описания пользователя
DESCRIPTION_PRESETS = [
    "Стандартный пользователь",
    "VIP-клиент",
    "Тестовый аккаунт",
    "Корпоративный клиент",
    "Демо-аккаунт"
]

# Полные шаблоны пользователей (комплексные пресеты)
USER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "🥉 Базовый": {
        "display_name": "🥉 Базовый тариф",
        "description": "Базовый пользователь VPN",
        "trafficLimitBytes": 100 * 1024 * 1024 * 1024,  # 100 ГБ
        "hwidDeviceLimit": 1,
        "trafficLimitStrategy": "MONTH",
        "resetDay": 1
    },
    "🥈 Стандартный": {
        "display_name": "🥈 Стандартный тариф",
        "description": "Стандартный пользователь VPN",
        "trafficLimitBytes": 300 * 1024 * 1024 * 1024,  # 300 ГБ
        "hwidDeviceLimit": 3,
        "trafficLimitStrategy": "MONTH",
        "resetDay": 1
    },
    "🥇 Премиум": {
        "display_name": "🥇 Премиум тариф",
        "description": "Премиум пользователь VPN",
        "trafficLimitBytes": 800 * 1024 * 1024 * 1024,  # 800 ГБ
        "hwidDeviceLimit": 5,
        "trafficLimitStrategy": "MONTH",
        "resetDay": 1
    },
    "👨‍👩‍👧‍👦 Семейный": {
        "display_name": "👨‍👩‍👧‍👦 Семейный тариф",
        "description": "Семейный тарифный план",
        "trafficLimitBytes": 1536 * 1024 * 1024 * 1024,  # 1.5 ТБ
        "hwidDeviceLimit": 10,
        "trafficLimitStrategy": "MONTH",
        "resetDay": 1
    },
    "🏢 Корпоративный": {
        "display_name": "🏢 Корпоративный тариф",
        "description": "Корпоративный тарифный план",
        "trafficLimitBytes": 0,  # Безлимитный
        "hwidDeviceLimit": 0,  # Без лимита устройств
        "trafficLimitStrategy": "NO_RESET",
        "resetDay": 1
    },
    "🧪 Тестовый": {
        "display_name": "🧪 Тестовый аккаунт",
        "description": "Тестовый аккаунт",
        "trafficLimitBytes": 10 * 1024 * 1024 * 1024,  # 10 ГБ
        "hwidDeviceLimit": 1,
        "trafficLimitStrategy": "WEEK",
        "resetDay": 1
    },
    "💎 VIP": {
        "display_name": "💎 VIP тариф",
        "description": "VIP клиент",
        "trafficLimitBytes": 0,  # Безлимитный
        "hwidDeviceLimit": 15,
        "trafficLimitStrategy": "NO_RESET",
        "resetDay": 1
    }
}

# Функции для работы с шаблонами
def get_template_names() -> List[str]:
    """Возвращает список ключей доступных шаблонов."""
    return list(USER_TEMPLATES.keys())

def get_template_display_names() -> List[str]:
    """Возвращает список отображаемых имен шаблонов."""
    return [template["display_name"] for template in USER_TEMPLATES.values()]

def get_template_by_name(name: str) -> Dict[str, Any]:
    """Возвращает шаблон по его ключу."""
    return USER_TEMPLATES.get(name, {}).copy()

def get_template_by_display_name(display_name: str) -> Dict[str, Any]:
    """Возвращает шаблон по его отображаемому имени."""
    for template in USER_TEMPLATES.values():
        if template["display_name"] == display_name:
            return template.copy()
    return {}

def apply_template_to_user_data(user_data: Dict[str, Any], template_name: str) -> Dict[str, Any]:
    """Применяет шаблон к данным пользователя, добавляя дату истечения по умолчанию."""
    template = get_template_by_name(template_name)
    if not template:
        return user_data
    
    # Копируем все данные из шаблона
    result = user_data.copy()
    for key, value in template.items():
        if key != "display_name":  # Не копируем служебное поле
            result[key] = value
    
    # Добавляем дату истечения по умолчанию (30 дней), если не указана
    if "expireAt" not in result:
        result["expireAt"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
    
    return result

def format_template_info(template_name: str) -> str:
    """Форматирует информацию о шаблоне для отображения пользователю."""
    template = get_template_by_name(template_name)
    if not template:
        return "Шаблон не найден"
    
    from modules.utils.formatters import format_bytes
    
    info = f"*{template['display_name']}*\n\n"
    
    # Форматируем трафик
    traffic = template.get("trafficLimitBytes", 0)
    if traffic == 0:
        traffic_str = "Безлимитный"
    else:
        traffic_str = format_bytes(traffic)
    
    # Форматируем устройства
    devices = template.get("hwidDeviceLimit", 0)
    if devices == 0:
        devices_str = "Без лимита"
    elif devices == 1:
        devices_str = "1 устройство"
    elif devices in [2, 3, 4]:
        devices_str = f"{devices} устройства"
    else:
        devices_str = f"{devices} устройств"
    
    # Форматируем стратегию сброса
    strategy = template.get("trafficLimitStrategy", "NO_RESET")
    strategy_map = {
        "NO_RESET": "Без сброса",
        "DAY": "Ежедневно",
        "WEEK": "Еженедельно", 
        "MONTH": "Ежемесячно"
    }
    strategy_str = strategy_map.get(strategy, strategy)
    
    info += f"📈 Трафик: {traffic_str}\n"
    info += f"📱 Устройства: {devices_str}\n"
    info += f"🔄 Сброс трафика: {strategy_str}\n"
    info += f"📝 Описание: {template.get('description', 'Не указано')}"
    
    return info
