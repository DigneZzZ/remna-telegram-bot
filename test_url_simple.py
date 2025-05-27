#!/usr/bin/env python3
"""
Простой тест форматирования URL подписки
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils.formatters import format_user_details

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

print("=== ТЕСТ ФОРМАТИРОВАНИЯ URL ПОДПИСКИ ===\n")

formatted_text = format_user_details(test_user)
print("РЕЗУЛЬТАТ:")
print(formatted_text)
print("\n=== КОНЕЦ ТЕСТА ===")
