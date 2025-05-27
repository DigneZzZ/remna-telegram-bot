#!/usr/bin/env python3
"""
Комплексный тест всех методов подключения к remnawave
"""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append('/app')

async def test_tcp():
    """Тест TCP подключения"""
    print(f"\n[{datetime.now()}] === TCP Connection Test ===")
    
    try:
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        result = sock.connect_ex(("remnawave", 3003))
        if result == 0:
            print("✅ TCP connection successful")
            sock.close()
            return True
        else:
            print(f"❌ TCP connection failed: {result}")
            sock.close()
            return False
            
    except Exception as e:
        print(f"❌ TCP test exception: {e}")
        return False

async def test_aiohttp():
    """Тест с aiohttp (наш основной клиент)"""
    print(f"\n[{datetime.now()}] === aiohttp Test ===")
    
    try:
        from modules.api.client import RemnaAPI
        
        result = await RemnaAPI.get('users', params={'size': 1})
        if result is not None:
            print("✅ aiohttp request successful")
            return True
        else:
            print("❌ aiohttp request failed (returned None)")
            return False
            
    except Exception as e:
        print(f"❌ aiohttp test exception: {e}")
        return False

async def test_httpx():
    """Тест с httpx"""
    print(f"\n[{datetime.now()}] === httpx Test ===")
    
    try:
        from modules.api.client_httpx import RemnaAPIHttpx
        
        result = await RemnaAPIHttpx.get('users', params={'size': 1})
        if result is not None:
            print("✅ httpx request successful")
            return True
        else:
            print("❌ httpx request failed (returned None)")
            return False
            
    except Exception as e:
        print(f"❌ httpx test exception: {e}")
        return False

async def test_requests():
    """Тест с обычными requests (синхронный)"""
    print(f"\n[{datetime.now()}] === requests Test ===")
    
    try:
        import requests
        from modules.config import API_BASE_URL, API_TOKEN
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{API_BASE_URL}/users",
            headers=headers,
            params={'size': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ requests successful")
            return True
        else:
            print(f"❌ requests failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ requests test exception: {e}")
        return False

async def test_curl_simulation():
    """Симуляция curl запроса"""
    print(f"\n[{datetime.now()}] === curl Simulation Test ===")
    
    try:
        import subprocess
        from modules.config import API_BASE_URL, API_TOKEN
        
        cmd = [
            'curl', '-s', '-w', '%{http_code}',
            '-H', f'Authorization: Bearer {API_TOKEN}',
            '-H', 'Content-Type: application/json',
            f'{API_BASE_URL}/users?size=1'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and '200' in result.stdout:
            print("✅ curl simulation successful")
            return True
        else:
            print(f"❌ curl simulation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ curl simulation exception: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 === Comprehensive Connection Test ===")
    print(f"Target: remnawave:3003")
    print(f"Time: {datetime.now()}")
    
    tests = [
        ("TCP", test_tcp()),
        ("aiohttp", test_aiohttp()),
        ("httpx", test_httpx()),
        ("requests", test_requests()),
        ("curl", test_curl_simulation())
    ]
    
    results = {}
    
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print(f"\n=== Final Results ===")
    success_count = 0
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if success:
            success_count += 1
    
    print(f"\n📊 Success rate: {success_count}/{len(results)}")
    
    if success_count == 0:
        print("\n🔍 All tests failed - this suggests:")
        print("1. Container 'remnawave' is not running")
        print("2. Network connectivity issues")
        print("3. Port 3003 is not accessible")
        print("4. API service is down")
    elif success_count < len(results):
        print(f"\n🔍 Partial success - some methods work")
        print("This suggests specific client configuration issues")
    else:
        print(f"\n🎉 All tests passed!")
    
    return success_count > 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
