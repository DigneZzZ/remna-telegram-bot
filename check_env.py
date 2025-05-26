#!/usr/bin/env python3
"""
Simple script to check environment variables
"""
import os
from dotenv import load_dotenv

def main():
    print("🔍 Checking environment variables...")
    
    # Load environment variables
    load_dotenv()
    
    # Check variables
    api_token = os.getenv("REMNAWAVE_API_TOKEN")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_user_ids_str = os.getenv("ADMIN_USER_IDS", "")
    api_base_url = os.getenv("API_BASE_URL")
    
    print(f"📍 API_BASE_URL: {'✅ Set' if api_base_url else '❌ Not set'}")
    if api_base_url:
        print(f"   Value: {api_base_url}")
    
    print(f"🔑 REMNAWAVE_API_TOKEN: {'✅ Set' if api_token else '❌ Not set'}")
    if api_token:
        print(f"   Length: {len(api_token)} characters")
    
    print(f"🤖 TELEGRAM_BOT_TOKEN: {'✅ Set' if bot_token else '❌ Not set'}")
    if bot_token:
        print(f"   Length: {len(bot_token)} characters")
    
    print(f"👑 ADMIN_USER_IDS: {'✅ Set' if admin_user_ids_str else '❌ Not set'}")
    if admin_user_ids_str:
        try:
            admin_user_ids = [int(id) for id in admin_user_ids_str.split(",") if id]
            print(f"   Parsed IDs: {admin_user_ids}")
            print(f"   Count: {len(admin_user_ids)}")
        except ValueError as e:
            print(f"   ❌ Error parsing IDs: {e}")
    
    # Check .env files
    print("\n📄 Environment files:")
    env_files = [".env", ".env.local", ".env.production"]
    for env_file in env_files:
        exists = os.path.exists(env_file)
        print(f"   {env_file}: {'✅ Exists' if exists else '❌ Not found'}")

if __name__ == "__main__":
    main()
