#!/usr/bin/env python3
import httpx
import asyncio
import logging
import sys

# Настраиваем детальное логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Включаем логирование httpx
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

async def minimal_auth_test():
    """Максимально упрощённый тест авторизации"""
    
    # МИНИМАЛЬНЫЕ заголовки - только самое необходимое
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InJlbW5hIiwiaWF0IjoxNzM2ODY2MDE5LCJleHAiOjE3Mzc0NzA4MTl9.0pGnInEwJayRU-6xvzJlPmdJdUC3P8Y1vwKwrEcfPsE"
    }
    
    # МАКСИМАЛЬНО простая конфигурация клиента
    client_config = {
        "timeout": 10.0,
        "verify": False,  # Отключаем SSL для HTTP
        "http1": True,    # Принудительно HTTP/1.1
        "http2": False,   # Отключаем HTTP/2
        "headers": headers,
        "limits": httpx.Limits(
            max_keepalive_connections=0,  # Без keepalive
            max_connections=1,
            keepalive_expiry=0
        )
    }
    
    url = "http://remnawave:3003/api/auth/me"
    
    logger.info(f"Testing connection to: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Client config: {client_config}")
    
    try:
        async with httpx.AsyncClient(**client_config) as client:
            logger.info("Client created successfully")
            
            # Отправляем простой GET запрос
            logger.info("Sending GET request...")
            response = await client.get(url)
            
            logger.info(f"SUCCESS! Status: {response.status_code}")
            logger.info(f"Headers: {dict(response.headers)}")
            logger.info(f"Content: {response.text[:200]}...")
            
            return response.status_code, response.text
            
    except httpx.RemoteProtocolError as e:
        logger.error(f"Remote protocol error: {e}")
        logger.error("Server disconnected without sending response")
        return None, str(e)
    except httpx.ConnectError as e:
        logger.error(f"Connection error: {e}")
        return None, str(e)
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error: {e}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None, str(e)

async def test_without_auth():
    """Тест без авторизации - может быть проблема в токене?"""
    
    # БЕЗ заголовков авторизации
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
    
    # Попробуем любой публичный endpoint
    url = "http://remnawave:3003/api/health"  # Возможно есть health check
    
    logger.info(f"Testing without auth to: {url}")
    
    try:
        async with httpx.AsyncClient(**client_config) as client:
            response = await client.get(url)
            logger.info(f"SUCCESS WITHOUT AUTH! Status: {response.status_code}")
            return response.status_code, response.text
            
    except Exception as e:
        logger.error(f"Failed without auth: {e}")
        
        # Попробуем корень
        try:
            url = "http://remnawave:3003/"
            logger.info(f"Trying root: {url}")
            response = await client.get(url)
            logger.info(f"ROOT SUCCESS! Status: {response.status_code}")
            return response.status_code, response.text
        except Exception as e2:
            logger.error(f"Root also failed: {e2}")
            return None, str(e2)

async def main():
    """Запускаем оба теста"""
    logger.info("=== TESTING WITHOUT AUTH ===")
    await test_without_auth()
    
    logger.info("\n=== TESTING WITH AUTH ===")
    await minimal_auth_test()

if __name__ == "__main__":
    asyncio.run(main())
