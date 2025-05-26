#!/usr/bin/env python3
"""
Тестовый скрипт для проверки индивидуального назначения inbound'ов пользователям
"""

import asyncio
import logging
from modules.api.users import UserAPI
from modules.api.inbounds import InboundAPI

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_individual_inbound_assignment():
    """Тестирует возможность индивидуального назначения inbound'ов"""
    
    print("🔍 Тестирование индивидуального назначения inbound'ов...")
    
    try:
        # 1. Получаем список пользователей
        print("\n📋 Получаем список пользователей...")
        users_response = await UserAPI.get_all_users()
        if not users_response or 'response' not in users_response:
            print("❌ Не удалось получить список пользователей")
            return
        
        users = users_response['response']['users'][:3]  # Берем первых 3 пользователей для теста
        print(f"✅ Найдено {len(users)} пользователей для тестирования")
        
        # Показываем текущие inbound'ы каждого пользователя
        for user in users:
            username = user.get('username', 'Unknown')
            active_inbounds = user.get('activeUserInbounds', [])
            print(f"   👤 {username}: {len(active_inbounds)} активных inbound'ов")
            for inbound in active_inbounds:
                if isinstance(inbound, dict):
                    tag = inbound.get('tag', 'No tag')
                    inbound_type = inbound.get('type', 'Unknown')
                    print(f"      - {tag} ({inbound_type})")
        
        # 2. Получаем список inbound'ов
        print("\n📋 Получаем список inbound'ов...")
        inbounds_response = await InboundAPI.get_all_inbounds()
        if not inbounds_response or 'response' not in inbounds_response:
            print("❌ Не удалось получить список inbound'ов")
            return
        
        inbounds = inbounds_response['response']['inbounds']
        print(f"✅ Найдено {len(inbounds)} inbound'ов")
        
        # Показываем доступные inbound'ы
        for inbound in inbounds[:5]:  # Показываем первые 5
            tag = inbound.get('tag', 'No tag')
            inbound_type = inbound.get('type', 'Unknown')
            uuid = inbound.get('uuid', 'No UUID')
            print(f"   🔗 {tag} ({inbound_type}) - {uuid}")
        
        if len(users) == 0 or len(inbounds) == 0:
            print("❌ Недостаточно данных для тестирования")
            return
        
        # 3. Тестируем назначение одного inbound'а одному пользователю
        test_user = users[0]
        test_inbound = inbounds[0]
        
        print(f"\n🧪 Тестируем назначение inbound'а '{test_inbound.get('tag')}' пользователю '{test_user.get('username')}'...")
        
        # Подготавливаем данные для обновления
        update_data = {
            "activeUserInbounds": [test_inbound['uuid']]  # Массив UUID inbound'ов
        }
        
        print(f"📤 Отправляем запрос на обновление пользователя...")
        print(f"   Данные: {update_data}")
        
        # Отправляем запрос
        result = await UserAPI.update_user(test_user['uuid'], update_data)
        
        if result:
            print("✅ Запрос успешно выполнен!")
            print(f"   Результат: {result}")
            
            # Проверяем, что изменения применились
            print("\n🔍 Проверяем обновленные данные пользователя...")
            updated_user = await UserAPI.get_user_by_uuid(test_user['uuid'])
            
            if updated_user and 'response' in updated_user:
                user_data = updated_user['response']
                active_inbounds = user_data.get('activeUserInbounds', [])
                print(f"   👤 {user_data.get('username')}: {len(active_inbounds)} активных inbound'ов")
                
                for inbound in active_inbounds:
                    if isinstance(inbound, dict):
                        tag = inbound.get('tag', 'No tag')
                        inbound_type = inbound.get('type', 'Unknown')
                        uuid = inbound.get('uuid', 'No UUID')
                        print(f"      - {tag} ({inbound_type}) - {uuid}")
                
                # Проверяем, что наш inbound присутствует
                assigned_uuids = [ib.get('uuid') for ib in active_inbounds if isinstance(ib, dict)]
                if test_inbound['uuid'] in assigned_uuids:
                    print("✅ Inbound успешно назначен пользователю!")
                else:
                    print("⚠️  Inbound не найден среди активных (возможно, заменил предыдущие)")
            else:
                print("❌ Не удалось получить обновленные данные пользователя")
        else:
            print("❌ Запрос не выполнен")
        
        # 4. Тестируем назначение нескольких inbound'ов одному пользователю
        if len(inbounds) > 1:
            print(f"\n🧪 Тестируем назначение нескольких inbound'ов пользователю '{test_user.get('username')}'...")
            
            # Берем первые два inbound'а
            multi_inbounds = [inbounds[0]['uuid'], inbounds[1]['uuid']]
            update_data = {
                "activeUserInbounds": multi_inbounds
            }
            
            print(f"📤 Отправляем запрос на назначение {len(multi_inbounds)} inbound'ов...")
            result = await UserAPI.update_user(test_user['uuid'], update_data)
            
            if result:
                print("✅ Запрос на множественное назначение успешно выполнен!")
                
                # Проверяем результат
                updated_user = await UserAPI.get_user_by_uuid(test_user['uuid'])
                if updated_user and 'response' in updated_user:
                    user_data = updated_user['response']
                    active_inbounds = user_data.get('activeUserInbounds', [])
                    assigned_uuids = [ib.get('uuid') for ib in active_inbounds if isinstance(ib, dict)]
                    
                    print(f"   📊 Результат: назначено {len(active_inbounds)} inbound'ов")
                    matches = sum(1 for uuid in multi_inbounds if uuid in assigned_uuids)
                    print(f"   ✅ Совпадений: {matches}/{len(multi_inbounds)}")
            else:
                print("❌ Запрос на множественное назначение не выполнен")
    
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    print("🚀 Запуск тестирования индивидуального назначения inbound'ов")
    asyncio.run(test_individual_inbound_assignment())
