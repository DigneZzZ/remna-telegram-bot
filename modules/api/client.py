import httpx
import logging
import json
import asyncio
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

def get_headers():
    """Get headers for API requests"""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
        # Убираем User-Agent и Accept - возможно сервер их не любит
    }

def get_client_kwargs():
    """Get httpx client configuration"""
    return {
        "timeout": 30.0,
        "verify": False if API_BASE_URL.startswith('http://') else True,
        "headers": get_headers(),
        # Отключаем keepalive полностью - возможно сервер его не поддерживает
        "limits": httpx.Limits(
            max_keepalive_connections=0,  # Отключаем keepalive
            max_connections=1,            # Только одно соединение
            keepalive_expiry=0            # Немедленно закрываем
        )
    }

class RemnaAPI:
    """API client for Remnawave API using httpx"""
    
    @staticmethod
    async def _make_request(method, endpoint, data=None, params=None, retry_count=3):
        """Make HTTP request with retry logic and proper error handling"""
        url = f"{API_BASE_URL}/{endpoint}"
        
        logger.info(f"Making {method} request to: {url}")
        logger.debug(f"Request params: {params}")
        logger.debug(f"Request data: {data}")
        
        for attempt in range(retry_count):
            try:
                client_kwargs = get_client_kwargs()
                logger.debug(f"Client config: {client_kwargs}")
                
                async with httpx.AsyncClient(**client_kwargs) as client:
                    request_kwargs = {
                        'url': url,
                        'params': params
                    }
                    
                    if method.upper() in ['POST', 'PATCH', 'PUT'] and data is not None:
                        request_kwargs['json'] = data
                    
                    response = await client.request(method, **request_kwargs)
                    
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    # Проверка статуса ответа
                    if response.status_code >= 500:
                        logger.warning(f"Server error {response.status_code}, retrying...")
                        if attempt < retry_count - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                    
                    response.raise_for_status()
                    
                    # Проверка Content-Type
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type.lower():
                        logger.error(f"Expected JSON but got {content_type}. Response: {response.text[:500]}")
                        return None
                    
                    # Парсинг JSON
                    if not response.text.strip():
                        logger.warning("Empty response received")
                        return None
                    
                    json_response = response.json()
                    
                    # Обработка структуры ответа Remnawave API
                    if isinstance(json_response, dict):
                        if 'response' in json_response:
                            return json_response['response']
                        elif 'error' in json_response:
                            logger.error(f"API returned error: {json_response['error']}")
                            return None
                        else:
                            return json_response
                    
                    return json_response
                        
            except httpx.ConnectError as e:
                logger.error(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {retry_count} attempts")
                    return None
                    
            except httpx.TimeoutException as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Timeout after {retry_count} attempts")
                    return None
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                if e.response.status_code >= 500 and attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Server error, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)
                else:
                    return None
        
        return None
    
    @staticmethod
    async def get(endpoint, params=None):
        """Make a GET request to the API"""
        return await RemnaAPI._make_request('GET', endpoint, params=params)
    
    @staticmethod
    async def post(endpoint, data=None):
        """Make a POST request to the API"""
        return await RemnaAPI._make_request('POST', endpoint, data=data)
    
    @staticmethod
    async def patch(endpoint, data=None):
        """Make a PATCH request to the API"""
        return await RemnaAPI._make_request('PATCH', endpoint, data=data)
    
    @staticmethod
    async def delete(endpoint, params=None):
        """Make a DELETE request to the API"""
        return await RemnaAPI._make_request('DELETE', endpoint, params=params)
