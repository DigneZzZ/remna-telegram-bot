#!/usr/bin/env python3
"""
Тестовый скрипт для проверки форматирования пользователя с реальными данными
"""

import sys
import logging
import json

# Добавляем путь к модулям
sys.path.append('.')

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_user_formatting():
    """Тестирование форматирования пользователя с данными из логов"""
    
    # Реальные данные пользователя из логов (обрезанные в логах, дополняем)
    test_user = {
        "uuid": "165bda06-bd89-4081-91b1-5f916f016c04",
        "username": "Tp9sReF8ZU2RPfnRfx0q",
        "shortUuid": "BhDmCNbdKxVxuGTn",
        "status": "ACTIVE",
        "expireAt": "2025-06-25T00:00:00.000Z",
        "createdAt": "2025-05-26T19:23:32.106Z",
        "updatedAt": "2025-05-27T07:39:02.239Z",
        "subscriptionUuid": "3a3da18f-6f0c-48dc-83f5-1f5dc9b92953",
        "usedTrafficBytes": 0,
        "lifetimeUsedTrafficBytes": 0,
        "trafficLimitBytes": 107374182400,
        "trafficLimitStrategy": "NO_RESET",
        "subLastUserAgent": None,
        "subLastOpenedAt": None,
        "onlineAt": None,
        # Добавляем возможный URL подписки (типичный формат)
        "subscriptionUrl": "https://p.far.ovh/sub/3a3da18f-6f0c-48dc-83f5-1f5dc9b92953?some_param=value&another=test"
    }
    
    print("🧪 Тестирование форматирования пользователя...")
    print("=" * 60)
    
    try:
        from modules.utils.formatters import format_user_details, escape_markdown
        
        # Тест 1: Обычное форматирование
        print("📋 Тест 1: Обычное форматирование")
        try:
            formatted_message = format_user_details(test_user)
            print(f"✅ Длина сообщения: {len(formatted_message)} символов")
            
            # Проверяем наличие URL подписки
            if 'subscriptionUrl' in formatted_message or 'URL подписки' in formatted_message:
                print("✅ URL подписки найден в сообщении")
            else:
                print("❌ URL подписки НЕ найден в сообщении")
            
            # Показываем первые 500 символов
            print(f"📄 Первые 500 символов:")
            print(formatted_message[:500])
            
            # Ищем проблемные символы около позиции 406 (из ошибки)
            if len(formatted_message) > 400:
                print(f"\n🔍 Символы около позиции 406:")
                start = max(0, 400)
                end = min(len(formatted_message), 420)
                problem_area = formatted_message[start:end]
                print(f"Позиции {start}-{end}: '{problem_area}'")
                
                # Проверяем на незакрытые Markdown теги
                backtick_count = problem_area.count('`')
                asterisk_count = problem_area.count('*')
                print(f"Backticks (`): {backtick_count}")
                print(f"Asterisks (*): {asterisk_count}")
                
        except Exception as e:
            print(f"❌ Ошибка при форматировании: {e}")
        
        print("\n" + "-" * 60)
        
        # Тест 2: Тестирование экранирования URL
        print("📋 Тест 2: Экранирование URL")
        test_urls = [
            "https://example.com/sub?param=value",
            "https://test.com/path_with_underscores",
            "https://site.com/path*with*asterisks",
            "https://url.com/with`backticks`",
            "https://complex.com/path?param1=val_1&param2=val*2&param3=val`3"
        ]
        
        for url in test_urls:
            escaped = escape_markdown(url)
            print(f"Original: {url}")
            print(f"Escaped:  {escaped}")
            print()
        
        print("\n" + "-" * 60)
        
        # Тест 3: Тестирование с различными URL
        print("📋 Тест 3: Форматирование с различными URL")
        
        for i, url in enumerate(test_urls, 1):
            test_user_copy = test_user.copy()
            test_user_copy['subscriptionUrl'] = url
            test_user_copy['username'] = f"test_user_{i}"
            
            try:
                formatted = format_user_details(test_user_copy)
                print(f"✅ Тест {i}: Успешно (длина: {len(formatted)} символов)")
                
                # Проверяем наличие URL
                if url in formatted or escape_markdown(url) in formatted:
                    print(f"✅ URL присутствует в сообщении")
                else:
                    print(f"❌ URL НЕ найден в сообщении")
                    
            except Exception as e:
                print(f"❌ Тест {i}: Ошибка - {e}")
            
            print()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что скрипт запускается из корневой директории проекта")

def main():
    print("🚀 Запуск тестирования форматирования пользователя")
    test_user_formatting()
    print("\n🎯 Тестирование завершено")

if __name__ == "__main__":
    main()
