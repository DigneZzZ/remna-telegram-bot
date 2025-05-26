#!/usr/bin/env python3
"""
Test admin user authorization
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_admin_config():
    """Test admin user configuration"""
    print("🔍 Проверка конфигурации ADMIN_USER_IDS")
    print("=" * 50)
    
    # Get raw value
    raw_admin_ids = os.getenv("ADMIN_USER_IDS", "")
    print(f"Raw ADMIN_USER_IDS: '{raw_admin_ids}'")
    
    # Parse admin IDs
    if raw_admin_ids:
        try:
            admin_ids = [int(id.strip()) for id in raw_admin_ids.split(",") if id.strip()]
            print(f"Parsed ADMIN_USER_IDS: {admin_ids}")
            print(f"Type of first ID: {type(admin_ids[0]) if admin_ids else 'No IDs'}")
            
            # Test authorization for known user
            test_user_id = 127192647
            print(f"\n🧪 Тест авторизации для пользователя {test_user_id}:")
            print(f"Is authorized: {test_user_id in admin_ids}")
            
            # Check all configured IDs
            print(f"\n👥 Все настроенные admin IDs:")
            for idx, admin_id in enumerate(admin_ids):
                print(f"  {idx + 1}. {admin_id} (type: {type(admin_id)})")
                
        except ValueError as e:
            print(f"❌ Ошибка парсинга ADMIN_USER_IDS: {e}")
    else:
        print("❌ ADMIN_USER_IDS пустой или не установлен!")
    
    # Test other important env vars
    print(f"\n🔧 Другие переменные:")
    print(f"API_BASE_URL: {os.getenv('API_BASE_URL', 'NOT SET')}")
    print(f"TELEGRAM_BOT_TOKEN: {'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT SET'}")
    print(f"REMNAWAVE_API_TOKEN: {'SET' if os.getenv('REMNAWAVE_API_TOKEN') else 'NOT SET'}")

if __name__ == "__main__":
    test_admin_config()
