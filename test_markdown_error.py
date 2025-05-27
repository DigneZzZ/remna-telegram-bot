#!/usr/bin/env python3
"""
Тест для диагностики ошибки Markdown на байте 406
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils.formatters import format_user_details, escape_markdown

# Тестовые данные пользователя
test_user = {
    'username': 'testuser',
    'uuid': '12345678-1234-1234-1234-123456789012',
    'shortUuid': 'abcd1234',
    'subscriptionUuid': '87654321-4321-4321-4321-210987654321',
    'subscriptionUrl': 'https://example.com/api/subscription/vless://12345678-1234-1234-1234-123456789012@server.example.com:443?encryption=none&security=tls&sni=server.example.com&type=ws&host=server.example.com&path=%2Fpath',
    'status': 'ACTIVE',
    'usedTrafficBytes': 1073741824,  # 1GB
    'trafficLimitBytes': 10737418240,  # 10GB
    'trafficLimitStrategy': 'BLOCK',
    'expireAt': '2024-12-31T23:59:59.000Z',
    'description': 'Test user description',
    'tag': 'test-tag',
    'telegramId': '123456789',
    'email': 'test@example.com',
    'hwidDeviceLimit': 5,
    'createdAt': '2024-01-01T00:00:00.000Z',
    'updatedAt': '2024-01-15T12:00:00.000Z'
}

def test_character_positions():
    """Тест для определения позиции байта 406"""
    print("Тестирование форматирования пользователя...")
    
    formatted_text = format_user_details(test_user)
    print(f"Общая длина текста: {len(formatted_text)} символов")
    print(f"Длина в байтах: {len(formatted_text.encode('utf-8'))} байт")
    
    # Показываем символ на позиции 406
    if len(formatted_text.encode('utf-8')) > 406:
        # Найдем позицию символа, который находится на байте 406
        byte_pos = 0
        char_pos = 0
        for i, char in enumerate(formatted_text):
            char_bytes = char.encode('utf-8')
            if byte_pos + len(char_bytes) > 406:
                print(f"\nСимвол на байте 406: '{char}' (позиция символа: {i})")
                print(f"Байты символа: {char_bytes}")
                
                # Показываем контекст вокруг этой позиции
                start = max(0, i - 20)
                end = min(len(formatted_text), i + 20)
                context = formatted_text[start:end]
                print(f"Контекст: '{context}'")
                
                # Показываем как байты
                context_bytes = context.encode('utf-8')
                print(f"Контекст в байтах: {context_bytes}")
                break
            byte_pos += len(char_bytes)
            char_pos = i
    
    print("\n" + "="*50)
    print("ФОРМАТИРОВАННЫЙ ТЕКСТ:")
    print("="*50)
    print(formatted_text)
    print("="*50)
    
    return formatted_text

def test_url_escaping():
    """Тест экранирования URL"""
    test_url = test_user['subscriptionUrl']
    print(f"\nОригинальный URL: {test_url}")
    print(f"Длина URL: {len(test_url)} символов")
    
    escaped_url = escape_markdown(test_url)
    print(f"\nЭкранированный URL: {escaped_url}")
    print(f"Длина экранированного URL: {len(escaped_url)} символов")
    
    # Подсчитаем разницу
    print(f"Добавлено символов экранирования: {len(escaped_url) - len(test_url)}")

if __name__ == "__main__":
    print("=== ТЕСТ ОШИБКИ MARKDOWN НА БАЙТЕ 406 ===\n")
    
    try:
        formatted_text = test_character_positions()
        test_url_escaping()
        
        print("\n=== ТЕСТ ЗАВЕРШЕН УСПЕШНО ===")
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
