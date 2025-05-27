import logging
from remnawave_api import RemnawaveSDK
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

class RemnawaveClient:
    """Clean SDK client for Remnawave API"""
    
    _instance = None
    _sdk = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._sdk is None:
            self._sdk = RemnawaveSDK(base_url=API_BASE_URL, token=API_TOKEN)
            logger.info(f"Initialized RemnawaveSDK with base_url: {API_BASE_URL}")
    
    @property
    def sdk(self):
        """Get SDK instance"""
        return self._sdk

# Singleton instance
_client = RemnawaveClient()

def get_remnawave_sdk():
    """Get RemnawaveSDK instance for direct usage"""
    return _client.sdk