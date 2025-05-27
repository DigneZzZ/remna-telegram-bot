import logging
import httpx
from remnawave_api import RemnawaveSDK
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

class RemnaAPI:
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_sdk'):
            logger.info(f"Initializing RemnawaveSDK with base_url: {API_BASE_URL}")
            
            try:
                self._sdk = RemnawaveSDK(
                    base_url=API_BASE_URL, 
                    token=API_TOKEN
                )
                
                # Добавляем reverse proxy заголовки
                if hasattr(self._sdk, '_client') and self._sdk._client:
                    proxy_headers = {
                        'X-Forwarded-Proto': 'https',
                        'X-Forwarded-For': '127.0.0.1',
                        'X-Real-IP': '127.0.0.1',
                    }
                    self._sdk._client.headers.update(proxy_headers)
                    logger.info("Added reverse proxy headers")
                
                logger.info("Successfully initialized RemnawaveSDK")
            except Exception as e:
                logger.error(f"Failed to initialize RemnawaveSDK: {e}")
                raise
    
    @classmethod
    def get_sdk(cls):
        instance = cls()
        return instance._sdk

def get_remnawave_sdk():
    return RemnaAPI.get_sdk()
