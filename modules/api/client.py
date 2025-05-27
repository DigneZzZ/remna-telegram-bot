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
            logger.info(f"Initializing RemnawaveSDK with base_url: {API_BASE_URL}, token_length: {len(API_TOKEN) if API_TOKEN else 0}")
            self._sdk = RemnawaveSDK(base_url=API_BASE_URL, token=API_TOKEN)
            logger.info(f"Successfully initialized RemnawaveSDK with base_url: {API_BASE_URL}")
    
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
        logger.warning(f"Legacy GET call to {endpoint} - consider migrating to SDK")
        # For now, return None to avoid errors
        return None
    
    @staticmethod  
    async def post(endpoint, data=None):
        """Legacy POST method - use SDK directly instead"""
        logger.warning(f"Legacy POST call to {endpoint} - consider migrating to SDK")
        # For now, return None to avoid errors
        return None
    
    @staticmethod
    async def patch(endpoint, data=None):
        """Legacy PATCH method - use SDK directly instead"""
        logger.warning(f"Legacy PATCH call to {endpoint} - consider migrating to SDK")
        # For now, return None to avoid errors  
        return None
    
    @staticmethod
    async def delete(endpoint):
        """Legacy DELETE method - use SDK directly instead"""
        logger.warning(f"Legacy DELETE call to {endpoint} - consider migrating to SDK")
        # For now, return None to avoid errors
        return None

# Legacy compatibility functions
def get_remnawave_sdk():
    """Get RemnawaveSDK instance for direct usage"""
    return RemnaAPI.get_sdk()