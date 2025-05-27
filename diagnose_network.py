#!/usr/bin/env python3
"""
Диагностический скрипт для проверки сетевого подключения
"""
import asyncio
import socket
import sys
import aiohttp
from datetime import datetime

async def test_tcp_connection(host, port):
    """Тест TCP соединения"""
    print(f"[{datetime.now()}] Testing TCP connection to {host}:{port}")
    
    try:
        # Создаем сокет и пытаемся подключиться
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ TCP connection to {host}:{port} successful")
            sock.close()
            return True
        else:
            print(f"❌ TCP connection failed with error code: {result}")
            sock.close()
            return False
            
    except Exception as e:
        print(f"❌ TCP connection exception: {e}")
        return False

async def test_http_simple(url):
    """Простой HTTP тест"""
    print(f"\n[{datetime.now()}] Testing simple HTTP connection to {url}")
    
    try:
        # Самый простой HTTP клиент
        connector = aiohttp.TCPConnector(
            ssl=False,
            limit=1,
            limit_per_host=1,
            force_close=True,  # Принудительно закрываем соединения
            keepalive_timeout=0  # Отключаем keepalive
        )
        
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            
            # Минимальные заголовки
            headers = {
                'User-Agent': 'Python/aiohttp',
                'Accept': '*/*'
            }
            
            async with session.get(url, headers=headers) as response:
                print(f"✅ HTTP response: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                text = await response.text()
                print(f"Response length: {len(text)}")
                return True
                
    except aiohttp.ServerDisconnectedError as e:
        print(f"❌ Server disconnected: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
        return False

async def test_dns_resolution(hostname):
    """Тест DNS разрешения"""
    print(f"\n[{datetime.now()}] Testing DNS resolution for {hostname}")
    
    try:
        # Разрешаем имя хоста
        loop = asyncio.get_event_loop()
        result = await loop.getaddrinfo(hostname, None)
        
        print(f"✅ DNS resolved {hostname} to:")
        for info in result:
            print(f"  - {info[4][0]}")
        return True
        
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

async def main():
    """Главная функция диагностики"""
    print("=== Network Diagnostics ===")
    
    hostname = "remnawave"
    port = 3003
    base_url = f"http://{hostname}:{port}"
    api_url = f"{base_url}/api"
    
    # Тест 1: DNS разрешение
    dns_ok = await test_dns_resolution(hostname)
    
    # Тест 2: TCP соединение
    tcp_ok = await test_tcp_connection(hostname, port)
    
    # Тест 3: HTTP соединение к базовому URL
    http_base_ok = await test_http_simple(base_url)
    
    # Тест 4: HTTP соединение к API
    http_api_ok = await test_http_simple(api_url)
    
    print(f"\n=== Results ===")
    print(f"DNS Resolution: {'✅' if dns_ok else '❌'}")
    print(f"TCP Connection: {'✅' if tcp_ok else '❌'}")
    print(f"HTTP Base: {'✅' if http_base_ok else '❌'}")
    print(f"HTTP API: {'✅' if http_api_ok else '❌'}")
    
    if not dns_ok:
        print("\n🔍 DNS resolution failed - check container network configuration")
    elif not tcp_ok:
        print("\n🔍 TCP connection failed - server may not be running or port blocked")
    elif not http_base_ok and not http_api_ok:
        print("\n🔍 HTTP connections failed - server may reject connections immediately")
    
    return all([dns_ok, tcp_ok, http_base_ok or http_api_ok])

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
