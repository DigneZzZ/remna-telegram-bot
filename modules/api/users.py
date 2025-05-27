import logging
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)

async def get_all_users():
    """Get all users using SDK with automatic pagination"""
    try:
        sdk = RemnaAPI.get_sdk()
        logger.info("Fetching all users via SDK")
        
        response = await sdk.users.get_all_users_v2()
        
        logger.info(f"Retrieved {response.total} users total via SDK")
        
        # Конвертируем в формат, ожидаемый остальным кодом
        return {
            'total': response.total,
            'users': [user.model_dump() for user in response.users]
        }
        
    except Exception as e:
        logger.error(f"Failed to get users via SDK: {e}")
        return {'total': 0, 'users': []}

async def get_users_count():
    """Get users count efficiently"""
    try:
        result = await get_all_users()
        return result.get('total', 0)
    except Exception as e:
        logger.error(f"Failed to get users count: {e}")
        return 0

async def get_users_stats():
    """Get users statistics"""
    try:
        result = await get_all_users()
        users = result.get('users', [])
        
        stats = {
            'total': len(users),
            'active': len([u for u in users if u.get('is_active', False)]),
            'disabled': len([u for u in users if not u.get('is_active', True)])
        }
        
        logger.info(f"Users stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get users stats: {e}")
        return {'total': 0, 'active': 0, 'disabled': 0}

