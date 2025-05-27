import logging
from remnawave_api import RemnawaveSDK
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

class RemnaAPI:
    """API client for Remnawave API using official SDK"""
    
    _sdk = None
    
    @classmethod
    def get_sdk(cls):
        """Get or create SDK instance"""
        if cls._sdk is None:
            cls._sdk = RemnawaveSDK(base_url=API_BASE_URL, token=API_TOKEN)
            logger.info(f"Initialized RemnawaveSDK with base_url: {API_BASE_URL}")
        return cls._sdk
    
    @staticmethod
    async def _make_request(method, endpoint, data=None, params=None, retry_count=3):
        """Legacy method for backward compatibility - delegates to SDK"""
        sdk = RemnaAPI.get_sdk()
        
        try:
            # Простая маршрутизация на основе endpoint
            if endpoint == 'users':
                response = await sdk.users.get_all_users_v2()
                return {
                    'total': response.total,
                    'users': [user.model_dump() for user in response.users]
                }
            elif endpoint == 'nodes':
                nodes = await sdk.nodes.get_all_nodes()
                return [node.model_dump() for node in nodes]
            elif endpoint.startswith('nodes/') and endpoint.endswith('/certificate'):
                node_uuid = endpoint.split('/')[1]
                cert = await sdk.nodes.get_node_certificate(node_uuid)
                return cert.model_dump()
            elif endpoint == 'nodes/usage/realtime':
                usage = await sdk.nodes.get_nodes_usage()
                return [u.model_dump() for u in usage]
            else:
                logger.warning(f"Unsupported endpoint for SDK: {endpoint}")
                return None
                
        except Exception as e:
            logger.error(f"SDK request failed for {endpoint}: {e}")
            raise
    
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
