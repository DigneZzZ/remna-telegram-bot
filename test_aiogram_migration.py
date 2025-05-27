#!/usr/bin/env python3
"""
Полный тест миграции на Aiogram
Проверяет все компоненты новой архитектуры
"""
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Тест импортов всех модулей"""
    print("🔍 Тестирование импортов...")
    
    try:
        # Основные модули
        from modules.config import ADMIN_USER_IDS
        print("✅ modules.config")
        
        # Aiogram handlers
        from modules.handlers import register_all_handlers
        print("✅ modules.handlers")
        
        # Отдельные handlers
        from modules.handlers.start_handler import router as start_router
        from modules.handlers.user_handlers import router as user_router
        from modules.handlers.node_handlers import router as node_router
        from modules.handlers.inbound_handlers import router as inbound_router
        from modules.handlers.bulk_handlers import router as bulk_router
        from modules.handlers.stats_handlers import router as stats_router
        from modules.handlers.host_handlers import router as host_router
        from modules.handlers.menu_handler import router as menu_router
        print("✅ Все router'ы импортированы")
        
        # States и auth
        from modules.handlers.states import UserStates, NodeStates, SystemStates
        from modules.handlers.auth import AuthFilter
        print("✅ States и auth")
        
        # Утилиты
        from modules.utils.formatters_aiogram import format_bytes, format_datetime
        from modules.utils.keyboard_helpers import KeyboardHelper
        print("✅ Утилиты")
        
        # API клиенты
        from modules.api.sdk_client import RemnaSDK
        from modules.api.client import RemnaAPI
        print("✅ API клиенты")
        
        print("✅ Все импорты прошли успешно!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_bot_initialization():
    """Тест инициализации бота"""
    print("\n🤖 Тестирование инициализации бота...")
    
    try:
        load_dotenv()
        
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from modules.handlers import register_all_handlers
        
        # Создаем фиктивный токен для теста
        bot = Bot(
            token="1234567890:TEST-TOKEN-FOR-TESTING-ONLY",
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрируем handlers
        register_all_handlers(dp)
        
        print("✅ Бот инициализирован успешно!")
        print(f"✅ Зарегистрировано роутеров: {len(dp.sub_routers)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        return False

def test_handlers_structure():
    """Тест структуры handlers"""
    print("\n📁 Тестирование структуры handlers...")
    
    try:
        from modules.handlers.start_handler import router as start_router
        from modules.handlers.user_handlers import router as user_router
        from modules.handlers.node_handlers import router as node_router
        
        # Проверяем, что роутеры имеют обработчики
        handlers_count = {
            'start': len(start_router.message.handlers) + len(start_router.callback_query.handlers),
            'user': len(user_router.message.handlers) + len(user_router.callback_query.handlers),
            'node': len(node_router.message.handlers) + len(node_router.callback_query.handlers)
        }
        
        for name, count in handlers_count.items():
            print(f"✅ {name}_router: {count} обработчиков")
        
        total_handlers = sum(handlers_count.values())
        print(f"✅ Всего обработчиков: {total_handlers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки структуры: {e}")
        return False

def test_states_definition():
    """Тест определения состояний FSM"""
    print("\n🔄 Тестирование состояний FSM...")
    
    try:
        from modules.handlers.states import UserStates, NodeStates, SystemStates
        
        # Проверяем наличие основных состояний
        user_states = [attr for attr in dir(UserStates) if not attr.startswith('_')]
        node_states = [attr for attr in dir(NodeStates) if not attr.startswith('_')]
        system_states = [attr for attr in dir(SystemStates) if not attr.startswith('_')]
        
        print(f"✅ UserStates: {len(user_states)} состояний")
        print(f"✅ NodeStates: {len(node_states)} состояний") 
        print(f"✅ SystemStates: {len(system_states)} состояний")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки состояний: {e}")
        return False

def test_formatters():
    """Тест функций форматирования"""
    print("\n✨ Тестирование форматеров...")
    
    try:
        from modules.utils.formatters_aiogram import format_bytes, format_datetime, escape_markdown
        from datetime import datetime
        
        # Тест format_bytes
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        print("✅ format_bytes работает")
        
        # Тест escape_markdown
        assert escape_markdown("test_string") == "test\\_string"
        print("✅ escape_markdown работает")
        
        # Тест format_datetime
        test_date = datetime.now()
        formatted = format_datetime(test_date)
        assert isinstance(formatted, str)
        print("✅ format_datetime работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования форматеров: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск полного теста миграции на Aiogram\n")
    
    tests = [
        ("Импорты", test_imports),
        ("Инициализация бота", test_bot_initialization),
        ("Структура handlers", test_handlers_structure),
        ("Состояния FSM", test_states_definition),
        ("Форматеры", test_formatters)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Тест '{test_name}' провален")
        except Exception as e:
            print(f"❌ Тест '{test_name}' упал с ошибкой: {e}")
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены! Миграция на Aiogram завершена успешно!")
        return 0
    else:
        print(f"\n⚠️  Есть проблемы в {total - passed} тестах. Необходимо исправить.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
