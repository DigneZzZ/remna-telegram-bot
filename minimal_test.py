#!/usr/bin/env python3
"""
Тест с точно такими же настройками как comprehensive_test
"""
import asyncio
import httpx
import sys
import os

# Добавляем путь к модулям
sys.path.append('/app' if os.path.exists('/app') else '.')

from modules.config import API_BASE_URL, API_TOKEN

async def test_minimal_httpx():
    """Тест с минимальными настройками как в comprehensive_test"""
    print(f"🧪 Testing minimal httpx settings...")
    print(f"API URL: {API_BASE_URL}")
    
    try:
        # Точно такие же настройки как в comprehensive_test
        client_kwargs = {
            "timeout": 30.0,
            "verify": False,
            "headers": {
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "application/json"
                # Никаких других заголовков!
            }
        }
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            url = f"{API_BASE_URL}/users"
            params = {'size': 1}
            
            print(f"Making request to: {url}")
            print(f"Headers: {client_kwargs['headers']}")
            print(f"Params: {params}")
            
            response = await client.get(url, params=params)
            
            print(f"✅ Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                return True
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def main():
    success = await test_minimal_httpx()
    print(f"\n{'✅ Test passed!' if success else '❌ Test failed!'}")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
