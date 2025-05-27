import logging
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
            self._sdk = RemnawaveSDK(base_url=API_BASE_URL, token=API_TOKEN)
            logger.info(f"Initialized RemnawaveSDK with base_url: {API_BASE_URL}")
    
    @classmethod
    def get_sdk(cls):
        """Get SDK instance - compatibility method"""
        instance = cls()
        return instance._sdk
    
    @property
    def sdk(self):
        """Get SDK instance"""
        return self._sdk

# Legacy compatibility functions
def get_remnawave_sdk():
    """Get RemnawaveSDK instance for direct usage"""
    return RemnaAPI.get_sdk()