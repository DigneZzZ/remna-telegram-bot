import aiohttp
import logging
import json
import asyncio
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

def get_headers():
    """Get headers for API requests"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "RemnaBot/1.0",
        "Accept": "application/json"
    }
    
    # Для HTTP соединений добавляем дополнительные заголовки
    if API_BASE_URL.startswith('http://'):
        headers.update({
            #"Connection": "close",  # Избегаем keep-alive для HTTP
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        })
        logger.debug("Added HTTP-specific headers")
    
    return headers

def get_connector():
    """Get connector with proper settings for Docker networking"""
    # Определяем настройки SSL на основе URL
    ssl_setting = None
    if API_BASE_URL.startswith('https://'):
        # Для HTTPS - используем SSL с проверкой сертификатов
        ssl_setting = True
        logger.debug(f"Using SSL verification for HTTPS URL: {API_BASE_URL}")
    elif API_BASE_URL.startswith('http://'):
        # Для HTTP - SSL не используется
        ssl_setting = False
        logger.debug(f"Disabling SSL for HTTP URL: {API_BASE_URL}")
    # Если схема не указана, используем по умолчанию без SSL для Docker
    else:
        ssl_setting = False
        logger.debug(f"No scheme in URL, disabling SSL: {API_BASE_URL}")
    
    # Дополнительные настройки для HTTP подключений
    connector_kwargs = {
        'ttl_dns_cache': 300,
        'use_dns_cache': True,
        'keepalive_timeout': 30,
        'enable_cleanup_closed': True,
        'limit': 10,
        'limit_per_host': 10,
        'ssl': ssl_setting
    }
    
    # Для HTTP подключений добавляем дополнительные настройки
    if API_BASE_URL.startswith('http://'):
        connector_kwargs.update({
            #'force_close': True,  # Принудительно закрывать соединения
            'enable_cleanup_closed': True
        })
        logger.debug("Added HTTP-specific connector settings")
    
    return aiohttp.TCPConnector(**connector_kwargs)

def get_timeout():
    """Get timeout settings"""
    return aiohttp.ClientTimeout(
        total=60,        # Общий таймаут
        connect=10,      # Таймаут подключения
        sock_read=30,    # Таймаут чтения
        sock_connect=10  # Таймаут сокет подключения
    )

class RemnaAPI:
    """API client for Remnawave API"""
    
    @staticmethod
    async def _make_request(method, endpoint, data=None, params=None, retry_count=3):
        """Make HTTP request with retry logic and proper error handling"""
        url = f"{API_BASE_URL}/{endpoint}"
        
        # Логируем настройки подключения
        logger.info(f"API Base URL: {API_BASE_URL}")
        logger.info(f"Full URL: {url}")
        logger.info(f"Method: {method}")
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Making {method} request to: {url} (attempt {attempt + 1}/{retry_count})")
                
                connector = get_connector()
                timeout = get_timeout()
                
                # Логируем настройки коннектора
                logger.debug(f"Connector SSL setting: {connector._ssl}")
                logger.debug(f"Timeout settings: connect={timeout.connect}, total={timeout.total}")
                logger.debug(f"Request headers: {get_headers()}")
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=get_headers(),
                    connector_owner=True,
                    ssl=False if API_BASE_URL.startswith('https://') else None
                ) as session:
                    
                    request_kwargs = {
                        'url': url,
                        'params': params
                    }
                    
                    if method.upper() in ['POST', 'PATCH', 'PUT'] and data is not None:
                        request_kwargs['json'] = data
                    
                    async with session.request(method, **request_kwargs) as response:
                        response_text = await response.text()
                        logger.debug(f"Response status: {response.status}")
                        logger.debug(f"Response headers: {dict(response.headers)}")
                        logger.debug(f"Response content (first 500 chars): {response_text[:500]}")
                        
                        # Проверка статуса ответа
                        if response.status >= 500:
                            logger.warning(f"Server error {response.status}, retrying...")
                            if attempt < retry_count - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        
                        response.raise_for_status()
                        
                        # Проверка Content-Type
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' not in content_type.lower():
                            logger.error(f"Expected JSON but got {content_type}. Response: {response_text[:500]}")
                            return None
                        
                        # Парсинг JSON
                        if not response_text.strip():
                            logger.warning("Empty response received")
                            return None
                            
                        json_response = await response.json()
                        
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
                        
            except aiohttp.ClientConnectorError as e:
                logger.error(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {retry_count} attempts")
                    return None
                    
            except aiohttp.ServerDisconnectedError as e:
                logger.error(f"Server disconnected on attempt {attempt + 1}: {str(e)}")
                logger.error(f"This usually means:")
                logger.error(f"1. Server only accepts HTTPS but we're using HTTP")
                logger.error(f"2. Server rejected the connection due to missing/wrong headers")
                logger.error(f"3. Server is not running on port {url.split(':')[-1].split('/')[0]}")
                logger.error(f"4. Network connectivity issues between containers")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Server disconnected after {retry_count} attempts")
                    return None
                    
            except aiohttp.ClientTimeout as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Timeout after {retry_count} attempts")
                    return None
                    
            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP error {e.status}: {e.message}")
                if e.status >= 500 and attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Server error, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error on attempt {attempt + 1}: {str(e)}")
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
