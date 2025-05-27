import logging
import httpx
from remnawave_api import RemnawaveSDK
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

class RemnaAPI:
    """Unified SDK client for Remnawave API"""
    
    _instance = None
    _sdk = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._sdk is None:
            # Подробное логирование параметров инициализации SDK
            logger.info(f"Initializing RemnawaveSDK with:")
            logger.info(f"- base_url: {API_BASE_URL}")
            logger.info(f"- token present: {bool(API_TOKEN)}")
            logger.info(f"- token length: {len(API_TOKEN) if API_TOKEN else 0}")
            
            if not API_TOKEN:
                logger.warning("API_TOKEN is missing! SDK initialization might fail")
            
            try:
                # Создаем кастомный HTTP клиент с заголовками reverse proxy
                # Это обходит проверку ProxyCheckMiddleware в RemnaWave
                headers = {
                    'X-Forwarded-Proto': 'https',
                    'X-Forwarded-For': '127.0.0.1',
                    'X-Real-IP': '127.0.0.1',
                    'Host': API_BASE_URL.replace('http://', '').replace('https://', '').split('/')[0]
                }
                
                logger.info(f"Creating HTTP client with reverse proxy headers: {headers}")
                
                # Создаем httpx клиент с кастомными заголовками
                http_client = httpx.AsyncClient(
                    headers=headers,
                    timeout=30.0,
                    verify=False  # Отключаем проверку SSL для внутренних запросов
                )
                
                self._sdk = RemnawaveSDK(
                    base_url=API_BASE_URL, 
                    token=API_TOKEN,
                    client=http_client
                )
                logger.info(f"Successfully initialized RemnawaveSDK with reverse proxy headers")
            except Exception as e:
                logger.error(f"Failed to initialize RemnawaveSDK: {e}")
                raise
    
    @classmethod
    def get_sdk(cls):
        """Get SDK instance - compatibility method"""
        logger.debug("RemnaAPI.get_sdk() called")
        instance = cls()
        return instance._sdk
    
    @property
    def sdk(self):
        """Get SDK instance"""
        return self._sdk
    
    # Legacy compatibility methods for old API classes
    @staticmethod
    async def get(endpoint, params=None):
        """Legacy GET method - use SDK directly instead"""
        logger.warning("Using legacy RemnaAPI.get() method - consider using SDK directly")
        sdk = RemnaAPI.get_sdk()
        # This would need to be implemented if actually used
        raise NotImplementedError("Legacy get method not implemented - use SDK directly")
    
    @staticmethod
    async def post(endpoint, data=None, json=None):
        """Legacy POST method - use SDK directly instead"""
        logger.warning("Using legacy RemnaAPI.post() method - consider using SDK directly")
        # This would need to be implemented if actually used
        raise NotImplementedError("Legacy post method not implemented - use SDK directly")

def get_remnawave_sdk():
    """Get the unified SDK instance"""
    return RemnaAPI.get_sdk()
