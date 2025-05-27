#!/usr/bin/env python3
"""
Тест unified API структуры
"""
import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(__file__))

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_unified_api():
    """Тест unified API структуры"""
    logger.info("=== Testing Unified API Structure ===")
    
    try:
        # Тест 1: Импорт unified client
        logger.info("Test 1: Importing unified client...")
        from modules.api.client import RemnaAPI
        sdk = RemnaAPI.get_sdk()
        logger.info(f"✅ SDK initialized: {type(sdk).__name__}")
        
        # Тест 2: Импорт API модулей
        logger.info("Test 2: Testing API modules...")
        from modules.api.users import get_all_users
        from modules.api.nodes import get_all_nodes
        logger.info("✅ API modules imported successfully")
        
        # Тест 3: Импорт handlers
        logger.info("Test 3: Testing handlers...")
        from modules.handlers.user_handlers import router as user_router
        from modules.handlers.start_handler import router as start_router
        from modules.handlers.node_handlers import router as node_router
        logger.info("✅ Handlers imported successfully")
        
        # Тест 4: Проверка legacy compatibility
        logger.info("Test 4: Testing legacy compatibility...")
        from modules.api.bulk import BulkAPI
        from modules.api.hosts import HostAPI
        logger.info("✅ Legacy API classes imported successfully")
        
        # Тест 5: Проверка SDK функциональности
        logger.info("Test 5: Testing SDK functionality...")
        users_response = await sdk.users.get_all_users_v2(size=5, start=0)
        logger.info(f"✅ SDK working: got {len(users_response.users)} users out of {users_response.total}")
        
        logger.info("🎉 All tests passed! Unified API structure is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Основная функция"""
    success = await test_unified_api()
    if success:
        logger.info("✅ Unified API test PASSED!")
    else:
        logger.error("❌ Unified API test FAILED!")
    return success

if __name__ == "__main__":
    asyncio.run(main())
