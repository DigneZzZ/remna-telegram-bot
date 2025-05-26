#!/usr/bin/env python3
"""
Check and fix API configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_api_config():
    """Check API configuration"""
    print("🔍 Проверка конфигурации API")
    print("=" * 40)
    
    api_base_url = os.getenv("API_BASE_URL", "")
    print(f"Текущий API_BASE_URL: {api_base_url}")
    
    # Check if URL looks correct
    if not api_base_url:
        print("❌ API_BASE_URL не установлен!")
        return False
    
    if not api_base_url.startswith(("http://", "https://")):
        print("❌ API_BASE_URL должен начинаться с http:// или https://")
        return False
    
    # Check if it ends with /api
    if api_base_url.endswith("/api"):
        print("✅ URL правильно заканчивается на /api")
    elif api_base_url.endswith("/"):
        print("⚠️  URL заканчивается на /, но не содержит /api")
        suggested = api_base_url + "api"
        print(f"💡 Предлагаемый URL: {suggested}")
    else:
        print("⚠️  URL не заканчивается на /api")
        suggested = api_base_url + "/api"
        print(f"💡 Предлагаемый URL: {suggested}")
    
    # Common URLs based on the domain
    domain = api_base_url.split("://")[1].split("/")[0] if "://" in api_base_url else api_base_url
    print(f"\n💡 Возможные правильные URL для домена {domain}:")
    print(f"   - https://{domain}/api")
    print(f"   - https://{domain}")
    
    return True

if __name__ == "__main__":
    check_api_config()
