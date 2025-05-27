#!/usr/bin/env python3
"""
Финальная проверка миграции с python-telegram-bot на Aiogram
Этот скрипт проверяет:
1. Корректность всех импортов
2. Инициализацию бота без токенов
3. Регистрацию всех обработчиков
4. Базовую структуру FSM
"""

import asyncio
import sys
import os
from unittest.mock import Mock

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Тестируем импорт всех необходимых модулей"""
    print("🔄 Проверка импортов...")
    
    try:
        # Базовые Aiogram импорты
        from aiogram import Bot, Dispatcher, Router
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.enums import ParseMode
        print("✅ Aiogram базовые модули")
        
        # Конфигурация
        from modules.config import ADMIN_USER_IDS, API_BASE_URL
        print("✅ modules.config")
        
        # Обработчики
        from modules.handlers.start_handler import register_start_handlers
        from modules.handlers.menu_handler import register_menu_handlers  
        from modules.handlers.user_handlers import register_user_handlers
        from modules.handlers.auth import AuthFilter
        print("✅ Все обработчики")
        
        # Основной файл
        import main_aiogram
        print("✅ main_aiogram.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_bot_initialization():
    """Тестируем инициализацию бота без реальных токенов"""
    print("\n🔄 Проверка инициализации...")
    
    try:
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        # Мокаем токен
        mock_token = "1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        
        # Создаем бота (это не запустит его, просто создаст объект)
        bot = Bot(
            token=mock_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        
        # Создаем диспетчер
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        print("✅ Инициализация Bot и Dispatcher")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

def test_handlers_registration():
    """Тестируем регистрацию всех обработчиков"""
    print("\n🔄 Проверка регистрации обработчиков...")
    
    try:
        from aiogram import Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from modules.handlers.start_handler import register_start_handlers
        from modules.handlers.menu_handler import register_menu_handlers
        from modules.handlers.user_handlers import register_user_handlers
        from modules.handlers.node_handlers import register_node_handlers
        from modules.handlers.stats_handlers import register_stats_handlers
        from modules.handlers.host_handlers import register_host_handlers
        from modules.handlers.inbound_handlers import register_inbound_handlers
        from modules.handlers.bulk_handlers import register_bulk_handlers
        
        # Создаем диспетчер
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрируем все обработчики
        register_start_handlers(dp)
        register_menu_handlers(dp)
        register_user_handlers(dp)
        register_node_handlers(dp)
        register_stats_handlers(dp)
        register_host_handlers(dp) 
        register_inbound_handlers(dp)
        register_bulk_handlers(dp)
        
        print("✅ Все обработчики зарегистрированы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка регистрации обработчиков: {e}")
        return False

def test_fsm_states():
    """Тестируем состояния FSM"""
    print("\n🔄 Проверка FSM состояний...")
    
    try:
        from modules.handlers.user_handlers import UserStates
        
        # Проверяем, что состояния определены
        assert hasattr(UserStates, 'waiting_for_search')
        assert hasattr(UserStates, 'waiting_for_username')
        
        print("✅ FSM состояния корректны")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка FSM: {e}")
        return False

def check_httpx_version():
    """Проверяем версию httpx для совместимости"""
    print("\n🔄 Проверка совместимости httpx...")
    
    try:
        import httpx
        version = httpx.__version__
        
        # Aiogram требует httpx >= 0.25.0
        # remnawave_api требует httpx >= 0.27.2
        # Должно быть >= 0.27.2
        major, minor, patch = map(int, version.split('.'))
        
        if major == 0 and minor >= 27:
            print(f"✅ httpx {version} совместим с обеими библиотеками")
            return True
        elif major > 0:
            print(f"✅ httpx {version} совместим с обеими библиотеками")
            return True
        else:
            print(f"⚠️  httpx {version} может быть несовместим")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки httpx: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("🚀 Финальная проверка миграции на Aiogram")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_bot_initialization,
        test_handlers_registration,
        test_fsm_states,
        check_httpx_version
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Миграция успешно завершена!")
        print("\n📋 Следующие шаги:")
        print("1. Добавьте реальные токены в .env файл")
        print("2. Запустите: python main_aiogram.py")
        print("3. Протестируйте с реальным ботом")
        print("4. Доработайте обработчики-заполнители")
        return True
    else:
        print("❌ Есть проблемы, которые нужно исправить")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
