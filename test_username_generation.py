#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генерации случайных имен пользователей
"""

import string
import random
from datetime import datetime

def generate_random_username():
    """Генерирует случайное имя пользователя (20 символов, буквы и цифры)"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(20))

def generate_default_description():
    """Генерирует описание по умолчанию"""
    return f"Автоматически созданный пользователь {datetime.now().strftime('%d.%m.%Y %H:%M')}"

def test_username_generation():
    """Тестирует генерацию имен пользователей"""
    print("🧪 Тестирование генерации случайных имен пользователей...\n")
    
    # Генерируем 5 тестовых имен
    for i in range(5):
        username = generate_random_username()
        description = generate_default_description()
        
        print(f"Тест {i+1}:")
        print(f"  📛 Имя пользователя: {username}")
        print(f"  📝 Описание: {description}")
        print(f"  📏 Длина имени: {len(username)} символов")
        
        # Проверяем, что имя содержит только буквы и цифры
        is_valid = all(c in string.ascii_letters + string.digits for c in username)
        print(f"  ✅ Валидность: {'Корректно' if is_valid else 'Ошибка'}")
        print()

def test_default_values():
    """Тестирует генерацию значений по умолчанию"""
    print("🧪 Тестирование значений по умолчанию...\n")
    
    # Симулируем user_data, как в реальном боте
    user_data = {}
    
    # Генерируем случайное имя пользователя, если не предоставлено
    if "username" not in user_data or not user_data.get("username"):
        characters = string.ascii_letters + string.digits
        random_username = ''.join(random.choice(characters) for _ in range(20))
        user_data["username"] = random_username
        print(f"🔤 Сгенерированное имя: {random_username}")
    
    # Устанавливаем значения по умолчанию
    if "trafficLimitStrategy" not in user_data:
        user_data["trafficLimitStrategy"] = "NO_RESET"
        print(f"📊 Стратегия сброса трафика: {user_data['trafficLimitStrategy']}")
    
    if "trafficLimitBytes" not in user_data:
        user_data["trafficLimitBytes"] = 100 * 1024 * 1024 * 1024  # 100 GB
        print(f"📈 Лимит трафика: {user_data['trafficLimitBytes']} байт (100 ГБ)")
    
    if "hwidDeviceLimit" not in user_data:
        user_data["hwidDeviceLimit"] = 1
        print(f"📱 Лимит устройств: {user_data['hwidDeviceLimit']}")
    
    if "description" not in user_data or not user_data.get("description"):
        user_data["description"] = f"Автоматически созданный пользователь {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        print(f"📝 Описание: {user_data['description']}")
    
    if "resetDay" not in user_data:
        user_data["resetDay"] = 1
        print(f"📅 День сброса: {user_data['resetDay']}")
    
    print(f"\n✅ Финальные данные пользователя:")
    for key, value in user_data.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    print("🚀 Запуск тестов генерации пользователей...\n")
    
    test_username_generation()
    print("=" * 50)
    test_default_values()
    
    print("\n🎉 Тестирование завершено!")
