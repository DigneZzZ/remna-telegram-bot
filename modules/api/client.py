import logging
import httpx
from typing import Dict, Any, Optional, Union
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

class RemnaAPI:
    """HTTP client for Remnawave API"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            logger.info(f"Initializing HTTP client for Remnawave API:")
            logger.info(f"- base_url: {API_BASE_URL}")
            logger.info(f"- token present: {bool(API_TOKEN)}")
            logger.info(f"- token length: {len(API_TOKEN) if API_TOKEN else 0}")
            
            if not API_TOKEN:
                logger.warning("API_TOKEN is missing! API calls might fail")
            
            try:
                # Создаем HTTP клиент с настройками
                self._client = httpx.AsyncClient(
                    base_url=API_BASE_URL,
                    timeout=30.0,
                    verify=False,  # Отключаем SSL verification для внутренних запросов
                    headers=self._get_default_headers()
                )
                
                logger.info("Successfully initialized HTTP client")
            except Exception as e:
                logger.error(f"Failed to initialize HTTP client: {e}")
                raise
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'RemnaBot/1.0'
        }
        
        # Добавляем токен авторизации если есть
        if API_TOKEN:
            headers['Authorization'] = f'Bearer {API_TOKEN}'
        
        # Добавляем reverse proxy заголовки
        headers.update({
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1',
            'Host': API_BASE_URL.replace('http://', '').replace('https://', '').split('/')[0]
        })
        
        return headers
    
    @classmethod
    async def get_client(cls):
        """Get HTTP client instance"""
        instance = cls()
        return instance._client
    
    @classmethod
    def get_sdk(cls):
        """Legacy compatibility method - returns HTTP client"""
        logger.debug("RemnaAPI.get_sdk() called (returning HTTP client)")
        instance = cls()
        return instance._client
    
    @property
    def client(self):
        """Get HTTP client instance"""
        return self._client
    
    # HTTP методы
    @staticmethod
    async def get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make GET request to API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        try:
            client = await RemnaAPI.get_client()
            
            # Убираем начальный слеш если есть
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            logger.debug(f"Making GET request to: {endpoint} with params: {params}")
            
            response = await client.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"GET {endpoint} successful")
                return data
            else:
                logger.error(f"GET {endpoint} failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making GET request to {endpoint}: {e}")
            return None
    
    @staticmethod
    async def post(endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make POST request to API
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json: JSON data
            
        Returns:
            JSON response or None if error
        """
        try:
            client = await RemnaAPI.get_client()
            
            # Убираем начальный слеш если есть
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            logger.debug(f"Making POST request to: {endpoint}")
            
            response = await client.post(endpoint, data=data, json=json)
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.debug(f"POST {endpoint} successful")
                return data
            else:
                logger.error(f"POST {endpoint} failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making POST request to {endpoint}: {e}")
            return None
    
    @staticmethod
    async def put(endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make PUT request to API
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json: JSON data
            
        Returns:
            JSON response or None if error
        """
        try:
            client = await RemnaAPI.get_client()
            
            # Убираем начальный слеш если есть
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            logger.debug(f"Making PUT request to: {endpoint}")
            
            response = await client.put(endpoint, data=data, json=json)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"PUT {endpoint} successful")
                return data
            else:
                logger.error(f"PUT {endpoint} failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making PUT request to {endpoint}: {e}")
            return None
    
    @staticmethod
    async def patch(endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make PATCH request to API
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json: JSON data
            
        Returns:
            JSON response or None if error
        """
        try:
            client = await RemnaAPI.get_client()
            
            # Убираем начальный слеш если есть
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            logger.debug(f"Making PATCH request to: {endpoint}")
            
            response = await client.patch(endpoint, data=data, json=json)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"PATCH {endpoint} successful")
                return data
            else:
                logger.error(f"PATCH {endpoint} failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making PATCH request to {endpoint}: {e}")
            return None
    
    @staticmethod
    async def delete(endpoint: str) -> bool:
        """Make DELETE request to API
        
        Args:
            endpoint: API endpoint (without base URL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await RemnaAPI.get_client()
            
            # Убираем начальный слеш если есть
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            logger.debug(f"Making DELETE request to: {endpoint}")
            
            response = await client.delete(endpoint)
            
            if response.status_code in [200, 204]:
                logger.debug(f"DELETE {endpoint} successful")
                return True
            else:
                logger.error(f"DELETE {endpoint} failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error making DELETE request to {endpoint}: {e}")
            return False
    
    @staticmethod
    async def close():
        """Close HTTP client"""
        instance = RemnaAPI()
        if instance._client:
            await instance._client.aclose()
            instance._client = None
            logger.info("HTTP client closed")

# Вспомогательные функции для обратной совместимости
def get_remnawave_sdk():
    """Get the HTTP client instance (legacy compatibility)"""
    return RemnaAPI.get_sdk()

async def get_http_client():
    """Get HTTP client instance"""
    return await RemnaAPI.get_client()

# Context manager для автоматического закрытия клиента
class RemnaAPIContext:
    """Context manager for RemnaAPI client"""
    
    def __init__(self):
        self.api = RemnaAPI()
    
    async def __aenter__(self):
        return self.api
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await RemnaAPI.close()

# Convenience функции для быстрых запросов
async def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Quick GET request"""
    return await RemnaAPI.get(endpoint, params)

async def api_post(endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Quick POST request"""
    return await RemnaAPI.post(endpoint, data, json)

async def api_put(endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Quick PUT request"""
    return await RemnaAPI.put(endpoint, data, json)

async def api_patch(endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Quick PATCH request"""
    return await RemnaAPI.patch(endpoint, data, json)

async def api_delete(endpoint: str) -> bool:
    """Quick DELETE request"""
    return await RemnaAPI.delete(endpoint)