#!/usr/bin/env python3
"""
Быстрая проверка статуса миграции
"""

def check_migration_status():
    print("🔍 Проверка статуса миграции...")
    print("=" * 40)
    
    # Проверка основных компонентов
    try:
        # 1. Проверка httpx
        import httpx
        print(f"✅ httpx версия: {httpx.__version__}")
        
        # 2. Проверка aiogram
        import aiogram
        print(f"✅ aiogram версия: {aiogram.__version__}")
        
        # 3. Проверка remnawave_api
        import remnawave_api
        print("✅ remnawave_api: OK")
        
        # 4. Проверка конфигурации
        from modules.config import ADMIN_USER_IDS
        print(f"✅ Админы настроены: {len(ADMIN_USER_IDS)} пользователей")
        
        # 5. Проверка основного файла
        import main_aiogram
        print("✅ main_aiogram.py: OK")
        
        print("\n🎉 Статус: Миграция успешна!")
        print("\n📋 Готов к запуску:")
        print("   python main_aiogram.py")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("⚠️  Требуется дополнительная настройка")

if __name__ == "__main__":
    check_migration_status()
