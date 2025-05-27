#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений Markdown и "Message is not modified"
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock
from modules.utils.formatters import format_user_details, safe_edit_message

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные пользователя
test_user = {
    'uuid': 'test-uuid-123-456-789',
    'shortUuid': 'test123',
    'subscriptionUuid': 'sub-uuid-123-456-789',
    'subscriptionUrl': 'https://very-long-subscription-url.example.com/path/to/subscription/with/very/long/path/and/parameters?param1=value1&param2=value2&param3=value3',
    'username': 'test_user_name',
    'status': 'ACTIVE',
    'usedTrafficBytes': 1073741824,  # 1GB
    'trafficLimitBytes': 10737418240,  # 10GB
    'trafficLimitStrategy': 'BLOCK_NEW_CONNECTIONS',
    'expireAt': '2025-06-27T12:00:00.000Z',
    'description': 'Тестовый пользователь с "кавычками" и *специальными* символами [test] (info)',
    'tag': 'test-tag',
    'telegramId': '123456789',
    'email': 'test@example.com',
    'hwidDeviceLimit': 3,
    'createdAt': '2025-05-27T12:00:00.000Z',
    'updatedAt': '2025-05-27T12:00:00.000Z'
}

async def test_format_user_details():
    """Тест форматирования данных пользователя"""
    logger.info("🧪 Тестируем форматирование данных пользователя...")
    
    try:
        # Тест с корректными данными
        message = format_user_details(test_user)
        logger.info("✅ Форматирование с корректными данными прошло успешно")
        logger.info(f"Длина сообщения: {len(message)} символов")
        
        # Проверим, что URL подписки включен
        if 'subscriptionUrl' in message or 'URL подписки' in message:
            logger.info("✅ URL подписки правильно включен в сообщение")
        else:
            logger.warning("⚠️ URL подписки не найден в сообщении")
        
        # Тест с проблемными символами
        problematic_user = test_user.copy()
        problematic_user['description'] = 'Test with _underscores_ and *asterisks* and `backticks` and [brackets]'
        problematic_user['username'] = 'user_with_special_chars_*_[_]_`'
        
        message_problematic = format_user_details(problematic_user)
        logger.info("✅ Форматирование с проблемными символами прошло успешно")
        
        # Тест с отсутствующими полями
        minimal_user = {
            'uuid': 'minimal-uuid',
            'username': 'minimal_user',
            'status': 'ACTIVE',
            'usedTrafficBytes': 0,
            'trafficLimitBytes': 1000000000,
            'trafficLimitStrategy': 'BLOCK_NEW_CONNECTIONS',
            'expireAt': '2025-06-27T12:00:00.000Z',
            'createdAt': '2025-05-27T12:00:00.000Z',
            'updatedAt': '2025-05-27T12:00:00.000Z'
        }
        
        message_minimal = format_user_details(minimal_user)
        logger.info("✅ Форматирование с минимальными данными прошло успешно")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании форматирования: {e}")
        return False

async def test_safe_edit_message():
    """Тест функции безопасного редактирования сообщений"""
    logger.info("🧪 Тестируем функцию safe_edit_message...")
    
    try:
        # Создаем mock объекты
        mock_query = Mock()
        mock_edit = AsyncMock()
        mock_answer = AsyncMock()
        mock_query.edit_message_text = mock_edit
        mock_query.answer = mock_answer
        
        # Тест успешного редактирования
        mock_edit.return_value = None
        result = await safe_edit_message(mock_query, "Test message", None, "Markdown")
        assert result == True
        logger.info("✅ Тест успешного редактирования прошел")
        
        # Тест с ошибкой "Message is not modified"
        mock_edit.side_effect = Exception("Message is not modified")
        result = await safe_edit_message(mock_query, "Test message", None, "Markdown")
        assert result == True  # Должен вернуть True, так как это ожидаемая ошибка
        logger.info("✅ Тест с ошибкой 'Message is not modified' прошел")
        
        # Тест с другой ошибкой
        mock_edit.side_effect = Exception("Some other error")
        result = await safe_edit_message(mock_query, "Test message", None, "Markdown")
        assert result == False  # Должен вернуть False для других ошибок
        logger.info("✅ Тест с другой ошибкой прошел")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании safe_edit_message: {e}")
        return False

async def test_markdown_escaping():
    """Тест экранирования Markdown символов"""
    logger.info("🧪 Тестируем экранирование Markdown символов...")
    
    from modules.utils.formatters import escape_markdown
    
    try:
        test_cases = [
            ("Hello_world", "Hello\\_world"),
            ("Test*text*", "Test\\*text\\*"),
            ("Code `sample`", "Code \\`sample\\`"),
            ("[Link](url)", "\\[Link\\]\\(url\\)"),
            ("Test_*_[_]_`_>_#_+_-_=_|_{_}_._!", "Test\\_\\*\\_\\[\\_\\]\\_\\`\\_\\>\\_\\#\\_\\+\\_\\-\\_\\=\\_\\|\\_\\{\\_\\}\\_\\.\\_\\!"),
        ]
        
        for input_text, expected in test_cases:
            result = escape_markdown(input_text)
            if result == expected:
                logger.info(f"✅ '{input_text}' -> '{result}'")
            else:
                logger.error(f"❌ '{input_text}' -> '{result}' (ожидалось: '{expected}')")
                return False
        
        logger.info("✅ Все тесты экранирования прошли успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании экранирования: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    logger.info("🚀 Запуск тестов исправлений...")
    
    tests = [
        ("Форматирование данных пользователя", test_format_user_details),
        ("Функция safe_edit_message", test_safe_edit_message),
        ("Экранирование Markdown", test_markdown_escaping),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Запуск теста: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ Тест '{test_name}' завершен успешно")
            else:
                logger.error(f"❌ Тест '{test_name}' провален")
        except Exception as e:
            logger.error(f"❌ Тест '{test_name}' вызвал исключение: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    logger.info("\n📊 ИТОГОВЫЙ ОТЧЕТ:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"  {status}: {test_name}")
    
    logger.info(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 Все тесты прошли успешно! Исправления работают корректно.")
    else:
        logger.warning("⚠️ Некоторые тесты провалены. Требуется дополнительная отладка.")

if __name__ == "__main__":
    asyncio.run(main())
