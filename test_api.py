#!/usr/bin/env python3
"""
Test API connectivity and authentication
"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://remna.st/api")
API_TOKEN = os.getenv("REMNAWAVE_API_TOKEN")

async def test_api():
    """Test API connectivity"""
    print("🔍 Тестирование API подключения")
    print("=" * 50)
    print(f"API_BASE_URL: {API_BASE_URL}")
    print(f"API_TOKEN: {'SET' if API_TOKEN else 'NOT SET'}")
    
    if not API_TOKEN:
        print("❌ API_TOKEN не установлен!")
        return
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints
    test_endpoints = [
        "api/users",
        "api/nodes", 
        "api/inbounds",
        "api/system/health"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in test_endpoints:
            url = f"{API_BASE_URL}/{endpoint}"
            print(f"\n🧪 Тестирование: {url}")
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"Status: {response.status}")
                    print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                    
                    response_text = await response.text()
                    print(f"Response length: {len(response_text)} bytes")
                    print(f"Response preview: {response_text[:200]}...")
                    
                    if response.status == 200:
                        print("✅ Успешно")
                    else:
                        print(f"❌ Ошибка: {response.status}")
                        
            except Exception as e:
                print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
