#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений Markdown parsing ошибок
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils.formatters import escape_markdown, format_user_details

def test_escape_markdown():
    """Тест функции escape_markdown"""
    print("=== Тест escape_markdown ===")
    
    test_cases = [
        "Normal text",
        "Text with _underscore_ and *asterisk*",
        "Text with [brackets] and (parentheses)",
        "Special chars: ~tilde~ `backtick` >greater #hash +plus -minus =equal |pipe {brace} .dot !exclamation",
        "Mixed: _test_ *bold* [link](url) `code` #title",
        None,
        "",
        "Это русский текст с символами: _ * [ ] ( ) ~ ` > # + - = | { } . !",
    ]
    
    for i, test in enumerate(test_cases):
        try:
            result = escape_markdown(test)
            print(f"Test {i+1}: '{test}' -> '{result}'")
        except Exception as e:
            print(f"Test {i+1}: '{test}' -> ERROR: {e}")
    
    print()

def test_format_user_details():
    """Тест функции format_user_details"""
    print("=== Тест format_user_details ===")
    
    # Тестовые данные пользователя с проблемными символами
    test_user = {
        'username': 'test_user_with_*special*_chars',
        'uuid': '12345678-1234-1234-1234-123456789abc',
        'shortUuid': 'abc123',
        'subscriptionUuid': '87654321-4321-4321-4321-cba987654321',
        'subscriptionUrl': 'https://example.com/subscribe?token=abc123_*special*_chars',
        'status': 'ACTIVE',
        'usedTrafficBytes': 1024000000,
        'trafficLimitBytes': 10240000000,
        'trafficLimitStrategy': 'BLOCK',
        'expireAt': '2025-12-31T23:59:59.000Z',
        'description': 'Test user with [special] chars and (parentheses) and _underscores_',
        'tag': 'test_tag_*with*_chars',
        'telegramId': '123456789',
        'email': 'test@example.com',
        'hwidDeviceLimit': 3,
        'createdAt': '2025-01-01T00:00:00.000Z',
        'updatedAt': '2025-01-15T12:00:00.000Z'
    }
    
    try:
        result = format_user_details(test_user)
        print("Formatted user details:")
        print(result)
        print("\n✅ format_user_details executed successfully")
    except Exception as e:
        print(f"❌ format_user_details failed: {e}")
    
    print()

def test_problematic_chars():
    """Тест проблемных символов, которые могут вызывать ошибки Markdown parsing"""
    print("=== Тест проблемных символов ===")
    
    problematic_texts = [
        "Text with byte offset issue: [some_link](http://example.com)",
        "Description: User with special chars _ * [ ] ( ) ~ ` > # + - = | { } . !",
        "Multi-line\ntext\nwith\nspecial chars",
        "Text ending at byte 391 position",
        "Текст на русском с символами: _ * [ ] ( ) и другими"
    ]
    
    for i, text in enumerate(problematic_texts):
        try:
            escaped = escape_markdown(text)
            print(f"Test {i+1}: Escaped successfully")
            print(f"  Original: {text}")
            print(f"  Escaped:  {escaped}")
        except Exception as e:
            print(f"Test {i+1}: Failed - {e}")
        print()

if __name__ == "__main__":
    print("🧪 Тестирование исправлений Markdown parsing ошибок\n")
    
    test_escape_markdown()
    test_format_user_details()
    test_problematic_chars()
    
    print("✅ Все тесты завершены!")
