#!/usr/bin/env python3
import httpx
import asyncio
import logging

# Настраиваем детальное логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_without_auth():
    """Тест без токена авторизации"""
    
    # Клиент БЕЗ заголовков авторизации
    client_config = {
        "timeout": 10.0,
        "verify": False,
        "http1": True,
        "http2": False,
        "limits": httpx.Limits(
            max_keepalive_connections=0,
            max_connections=1,
            keepalive_expiry=0
        )
    }
    
    endpoints_to_test = [
        "http://remnawave:3003/",           # Корень
        "http://remnawave:3003/api/",       # API корень  
        "http://remnawave:3003/health",     # Health check
        "http://remnawave:3003/api/health", # API health
        "http://remnawave:3003/api/users",  # Пользователи без токена
        "http://remnawave:3003/api/nodes",  # Ноды без токена
    ]
    
    async with httpx.AsyncClient(**client_config) as client:
        for url in endpoints_to_test:
            logger.info(f"\n=== Testing: {url} ===")
            try:
                response = await client.get(url)
                logger.info(f"✅ SUCCESS! Status: {response.status_code}")
                logger.info(f"Headers: {dict(response.headers)}")
                content = response.text[:300]
                logger.info(f"Content preview: {content}...")
                
                if response.status_code == 200:
                    logger.info("🎉 WORKING ENDPOINT FOUND!")
                    return url, response.status_code, response.text
                    
            except httpx.RemoteProtocolError as e:
                logger.error(f"❌ RemoteProtocolError: {e}")
            except httpx.ConnectError as e:
                logger.error(f"❌ Connection error: {e}")
            except Exception as e:
                logger.error(f"❌ Other error: {e}")
    
    return None, None, None

async def test_minimal_headers():
    """Тест с минимальными заголовками (без Authorization)"""
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "RemnaBot/1.0"
    }
    
    client_config = {
        "timeout": 10.0,
        "verify": False,
        "headers": headers,
        "limits": httpx.Limits(
            max_keepalive_connections=0,
            max_connections=1,
            keepalive_expiry=0
        )
    }
    
    url = "http://remnawave:3003/api/users"
    
    logger.info(f"\n=== Testing with minimal headers: {url} ===")
    logger.info(f"Headers: {headers}")
    
    try:
        async with httpx.AsyncClient(**client_config) as client:
            response = await client.get(url)
            logger.info(f"✅ SUCCESS! Status: {response.status_code}")
            return response.status_code, response.text
            
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        return None, str(e)

async def test_different_auth_formats():
    """Тест разных форматов авторизации"""
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiMjhkMDk1ZjQtOTVlMC00YmU4LWE4ZDYtNTExYTQxM2Y3YTVkIiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3NDgzMzYxMzIsImV4cCI6MTAzODgyNDk3MzJ9.fy8vRC_RepWwn6VsAhddyYaX2y_h6DE0I6dYMLB0KZg"
    
    auth_variants = [
        {"Authorization": f"Bearer {token}"},
        {"Authorization": f"JWT {token}"},
        {"Authorization": token},
        {"X-API-Key": token},
        {"X-Auth-Token": token},
        {"Token": token},
    ]
    
    url = "http://remnawave:3003/api/users"
    
    for i, headers in enumerate(auth_variants):
        logger.info(f"\n=== Auth variant {i+1}: {headers} ===")
        
        client_config = {
            "timeout": 10.0,
            "verify": False,
            "headers": headers,
            "limits": httpx.Limits(
                max_keepalive_connections=0,
                max_connections=1,
                keepalive_expiry=0
            )
        }
        
        try:
            async with httpx.AsyncClient(**client_config) as client:
                response = await client.get(url)
                logger.info(f"✅ SUCCESS! Status: {response.status_code}")
                if response.status_code == 200:
                    logger.info("🎉 WORKING AUTH FORMAT FOUND!")
                    return headers, response.status_code, response.text
                    
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
    
    return None, None, None

async def main():
    """Запускаем все тесты"""
    logger.info("🔍 Testing Remnawave API without authentication...")
    
    # Тест без авторизации
    result = await test_without_auth()
    if result[0]:
        logger.info(f"✅ Found working endpoint: {result[0]}")
        return
    
    # Тест с минимальными заголовками
    logger.info("\n🔍 Testing with minimal headers...")
    await test_minimal_headers()
    
    # Тест разных форматов авторизации
    logger.info("\n🔍 Testing different auth formats...")
    auth_result = await test_different_auth_formats()
    if auth_result[0]:
        logger.info(f"✅ Found working auth format: {auth_result[0]}")

if __name__ == "__main__":
    asyncio.run(main())
