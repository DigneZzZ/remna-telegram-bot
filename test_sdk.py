#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, '/opt/app')

# Настраиваем детальное логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Устанавливаем переменные окружения
os.environ['REMNAWAVE_BASE_URL'] = 'http://remnawave:3003'
os.environ['REMNAWAVE_TOKEN'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiMjhkMDk1ZjQtOTVlMC00YmU4LWE4ZDYtNTExYTQxM2Y3YTVkIiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3NDgzMzYxMzIsImV4cCI6MTAzODgyNDk3MzJ9.fy8vRC_RepWwn6VsAhddyYaX2y_h6DE0I6dYMLB0KZg'

async def test_sdk():
    """Тест официального SDK"""
    try:
        from remnawave_api import RemnawaveSDK
        
        # Инициализируем SDK
        sdk = RemnawaveSDK(
            base_url="http://remnawave:3003",
            token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiMjhkMDk1ZjQtOTVlMC00YmU4LWE4ZDYtNTExYTQxM2Y3YTVkIiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3NDgzMzYxMzIsImV4cCI6MTAzODgyNDk3MzJ9.fy8vRC_RepWwn6VsAhddyYaX2y_h6DE0I6dYMLB0KZg"
        )
        
        logger.info("SDK initialized successfully")
        
        # Тестируем получение пользователей
        logger.info("Testing get_all_users_v2...")
        response = await sdk.users.get_all_users_v2(size=10, start=0)
        
        logger.info(f"SUCCESS! Got {len(response.users)} users out of {response.total} total")
        
        for user in response.users[:3]:  # Показываем первых 3 пользователей
            logger.info(f"User: {user.username} ({user.uuid})")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import SDK: {e}")
        return False
    except Exception as e:
        logger.error(f"SDK test failed: {e}")
        return False

async def main():
    """Основная функция"""
    logger.info("=== Testing Remnawave SDK ===")
    
    success = await test_sdk()
    
    if success:
        logger.info("✅ SDK test PASSED!")
    else:
        logger.error("❌ SDK test FAILED!")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
