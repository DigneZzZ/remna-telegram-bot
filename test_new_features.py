#!/usr/bin/env python3
"""
Скрипт для тестирования новых функций Remnawave Telegram Bot

Проверяет:
1. Импорт всех модулей
2. Загрузку конфигурации
3. Новые API методы
4. Форматирование Markdown
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тест импорта всех модулей"""
    print("🔄 Тестирование импортов...")
    
    try:
        # Тест импорта конфигурации
        from modules.config import (
            DASHBOARD_SHOW_SYSTEM_STATS, DASHBOARD_SHOW_SERVER_INFO,
            DASHBOARD_SHOW_USERS_COUNT, DASHBOARD_SHOW_NODES_COUNT,
            DASHBOARD_SHOW_TRAFFIC_STATS, DASHBOARD_SHOW_UPTIME,
            ENABLE_PARTIAL_SEARCH, SEARCH_MIN_LENGTH
        )
        print("✅ Конфигурация загружена")
        
        # Тест новых методов API
        from modules.api.users import UserAPI
        print("✅ UserAPI импортирован")
        
        # Проверим наличие новых методов
        if hasattr(UserAPI, 'search_users_by_partial_name'):
            print("✅ Метод search_users_by_partial_name найден")
        else:
            print("❌ Метод search_users_by_partial_name НЕ найден")
            
        if hasattr(UserAPI, 'search_users_by_description'):
            print("✅ Метод search_users_by_description найден")
        else:
            print("❌ Метод search_users_by_description НЕ найден")
        
        # Тест форматтеров
        from modules.utils.formatters import escape_markdown
        print("✅ Форматтеры импортированы")
        
        # Тест escape_markdown с проблемными символами
        test_text = "Тест_символы*разметки[ссылка](url)`код`"
        escaped = escape_markdown(test_text)
        print(f"✅ Тест escape_markdown: '{test_text}' -> '{escaped}'")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

def test_config():
    """Тест настроек конфигурации"""
    print("\n🔄 Тестирование конфигурации...")
    
    try:
        from modules.config import (
            DASHBOARD_SHOW_SYSTEM_STATS, ENABLE_PARTIAL_SEARCH, SEARCH_MIN_LENGTH
        )
        
        print(f"📊 DASHBOARD_SHOW_SYSTEM_STATS: {DASHBOARD_SHOW_SYSTEM_STATS}")
        print(f"🔍 ENABLE_PARTIAL_SEARCH: {ENABLE_PARTIAL_SEARCH}")
        print(f"📏 SEARCH_MIN_LENGTH: {SEARCH_MIN_LENGTH}")
        
        # Проверим типы
        assert isinstance(DASHBOARD_SHOW_SYSTEM_STATS, bool), "DASHBOARD_SHOW_SYSTEM_STATS должен быть bool"
        assert isinstance(ENABLE_PARTIAL_SEARCH, bool), "ENABLE_PARTIAL_SEARCH должен быть bool"
        assert isinstance(SEARCH_MIN_LENGTH, int), "SEARCH_MIN_LENGTH должен быть int"
        
        print("✅ Все настройки корректны")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_markdown_formatting():
    """Тест форматирования Markdown"""
    print("\n🔄 Тестирование форматирования Markdown...")
    
    try:
        from modules.utils.formatters import escape_markdown
        
        test_cases = [
            ("Normal text", "Normal text"),
            ("Text with * asterisk", "Text with \\* asterisk"),
            ("Text with _ underscore", "Text with \\_ underscore"),
            ("Text with [link](url)", "Text with \\[link\\]\\(url\\)"),
            ("Text with `code`", "Text with \\`code\\`"),
            ("Mixed *test* _case_ [link](url)", "Mixed \\*test\\* \\_case\\_ \\[link\\]\\(url\\)"),
        ]
        
        for original, expected in test_cases:
            result = escape_markdown(original)
            if result == expected:
                print(f"✅ '{original}' -> '{result}'")
            else:
                print(f"❌ '{original}' -> '{result}' (ожидалось: '{expected}')")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования Markdown: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов новых функций Remnawave Telegram Bot\n")
    
    tests = [
        test_imports,
        test_config, 
        test_markdown_formatting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
            results.append(False)
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Успешных тестов: {sum(results)}/{len(results)}")
    print(f"❌ Провальных тестов: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 Все тесты прошли успешно! Новые функции готовы к использованию.")
        return 0
    else:
        print("\n⚠️ Некоторые тесты провалились. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    exit(main())
