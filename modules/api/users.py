import logging
import httpx
from modules.api.client import RemnaAPI
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

def _get_headers():
    """Получить стандартные заголовки для API запросов"""
    return {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json',
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-For': '127.0.0.1',
        'X-Real-IP': '127.0.0.1'
    }

async def get_all_users():
    """Получить всех пользователей через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # Используем правильный endpoint без лишних параметров
            url = f"{API_BASE_URL}/users"
            logger.info(f"Making direct API call to: {url}")
              response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # Проверяем структуру ответа
                if isinstance(data, dict) and 'users' in data:
                    users_list = data['users']
                elif isinstance(data, list):
                    users_list = data
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
                
                logger.info(f"Retrieved {len(users_list)} users successfully")
                return users_list
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

async def get_user_by_uuid(user_uuid: str):
    """Получить пользователя по UUID"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Retrieved user: {user_data.get('username', user_uuid)}")
                return user_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting user {user_uuid}: {e}")
        return None

async def enable_user(user_uuid: str):
    """Включить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}/enable"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Enabled user: {user_data.get('username', user_uuid)}")
                return user_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling user {user_uuid}: {e}")
        return None

async def disable_user(user_uuid: str):
    """Отключить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}/disable"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Disabled user: {user_data.get('username', user_uuid)}")
                return user_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling user {user_uuid}: {e}")
        return None

async def delete_user(user_uuid: str):
    """Удалить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.delete(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"Deleted user: {user_uuid}")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting user {user_uuid}: {e}")
        return False

async def reset_user_traffic(user_uuid: str):
    """Сбросить трафик пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}/reset-traffic"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Reset traffic for user: {user_data.get('username', user_uuid)}")
                return user_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error resetting traffic for user {user_uuid}: {e}")
        return None

async def revoke_user_subscription(user_uuid: str):
    """Отозвать подписку пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}/revoke-subscription"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Revoked subscription for user: {user_data.get('username', user_uuid)}")
                return user_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error revoking subscription for user {user_uuid}: {e}")
        return None

async def get_users_count():
    """Получить количество пользователей"""
    try:
        users = await get_all_users()
        return len(users) if users else 0
    except Exception as e:
        logger.error(f"Error getting users count: {e}")
        return 0

async def get_users_stats():
    """Получить статистику пользователей"""
    try:
        users = await get_all_users()
        if not users:
            return None
            
        total_users = len(users)
        active_users = 0
        
        # Подсчитываем активных пользователей
        for user in users:
            if isinstance(user, dict):
                if user.get('is_active'):
                    active_users += 1
                elif user.get('status') == 'active':
                    active_users += 1
        
        return {
            'total': total_users,
            'active': active_users
        }
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        return None
