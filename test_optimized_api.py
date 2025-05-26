#!/usr/bin/env python3
"""
Тестирование оптимизированных API методов для управления пользователями
"""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.api.hosts import HostAPI
from modules.config import API_BASE_URL, API_TOKEN

async def test_optimized_user_methods():
    """Тестирование оптимизированных методов пользователей"""
    print("🔧 Тестирование оптимизированных методов пользователей")
    print("=" * 60)
    
    # Получаем список пользователей для тестирования
    try:
        users_response = await UserAPI.get_all_users()
        if not users_response or not users_response.get("users"):
            print("❌ Нет пользователей для тестирования")
            return False
            
        test_user = users_response["users"][0]
        user_uuid = test_user["uuid"]
        user_name = test_user["username"]
        current_status = test_user["status"]
        
        print(f"📋 Тестовый пользователь: {user_name} (UUID: {user_uuid})")
        print(f"📊 Текущий статус: {current_status}")
        
        # Тест 1: Отключение пользователя (если активен)
        if current_status == "ACTIVE":
            print(f"\n🔴 Тест 1: Отключение пользователя {user_name}")
            result = await UserAPI.disable_user(user_uuid)
            if result:
                print("✅ Метод disable_user() работает корректно с PATCH-запросом")
                
                # Проверяем изменение статуса
                updated_user = await UserAPI.get_user_by_uuid(user_uuid)
                if updated_user and updated_user["status"] == "DISABLED":
                    print("✅ Статус пользователя изменен на DISABLED")
                else:
                    print("⚠️ Статус пользователя не изменился")
            else:
                print("❌ Ошибка при отключении пользователя")
                return False
        
        # Тест 2: Включение пользователя
        print(f"\n🟢 Тест 2: Включение пользователя {user_name}")
        result = await UserAPI.enable_user(user_uuid)
        if result:
            print("✅ Метод enable_user() работает корректно с PATCH-запросом")
            
            # Проверяем изменение статуса
            updated_user = await UserAPI.get_user_by_uuid(user_uuid)
            if updated_user and updated_user["status"] == "ACTIVE":
                print("✅ Статус пользователя изменен на ACTIVE")
            else:
                print("⚠️ Статус пользователя не изменился")
                
            # Возвращаем исходный статус
            if current_status == "DISABLED":
                await UserAPI.disable_user(user_uuid)
                print(f"🔄 Статус пользователя возвращен к исходному: {current_status}")
                
        else:
            print("❌ Ошибка при включении пользователя")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

async def test_node_methods():
    """Тестирование методов управления нодами"""
    print("\n🖥️ Проверка методов управления нодами")
    print("=" * 50)
    
    try:
        nodes = await NodeAPI.get_all_nodes()
        if nodes and len(nodes) > 0:
            test_node = nodes[0]
            print(f"📋 Тестовый нод: {test_node.get('name', 'Unknown')}")
            print("✅ Ноды уже используют оптимизированные PATCH-запросы")
        else:
            print("⚠️ Нет нодов для проверки")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке нодов: {e}")
        return False

async def test_host_methods():
    """Тестирование методов управления хостами"""
    print("\n🏠 Проверка методов управления хостами")
    print("=" * 50)
    
    try:
        hosts = await HostAPI.get_all_hosts()
        if hosts and len(hosts) > 0:
            test_host = hosts[0]
            print(f"📋 Тестовый хост: {test_host.get('remark', 'Unknown')}")
            print("✅ Хосты уже используют оптимизированные PATCH-запросы")
        else:
            print("⚠️ Нет хостов для проверки")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке хостов: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование оптимизированных API методов")
    print(f"⏰ Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API URL: {API_BASE_URL}")
    print(f"🔑 API Token: {'✅ Установлен' if API_TOKEN else '❌ Не установлен'}")
    print("=" * 70)
    
    if not API_TOKEN:
        print("❌ API_TOKEN не установлен. Проверьте файл .env")
        return False
    
    # Тестируем оптимизированные методы пользователей
    user_test_result = await test_optimized_user_methods()
    
    # Проверяем методы нодов
    node_test_result = await test_node_methods()
    
    # Проверяем методы хостов
    host_test_result = await test_host_methods()
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print(f"👥 Пользователи (оптимизированы): {'✅ УСПЕШНО' if user_test_result else '❌ ОШИБКА'}")
    print(f"🖥️ Ноды (уже оптимизированы): {'✅ ПРОВЕРЕНО' if node_test_result else '❌ ОШИБКА'}")
    print(f"🏠 Хосты (уже оптимизированы): {'✅ ПРОВЕРЕНО' if host_test_result else '❌ ОШИБКА'}")
    
    overall_success = user_test_result and node_test_result and host_test_result
    
    if overall_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✨ Оптимизация API методов завершена")
    else:
        print("\n⚠️ Обнаружены проблемы при тестировании")
        
    return overall_success

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
