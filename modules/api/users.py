import logging
import httpx
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

async def get_all_users():
    """Получить всех пользователей через прямой HTTP вызов"""
    try:
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/users",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data and 'users' in data['response']:
                logger.info(f"Retrieved {data['response'].get('total', len(data['response']['users']))} users total")
                return data['response']['users']
            else:
                logger.error(f"Unexpected response structure: {data}")
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
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/users/{user_uuid}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Retrieved user: {data['response'].get('username', user_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
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
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/users/{user_uuid}/actions/enable",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Enabled user: {data['response'].get('username', user_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
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
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/users/{user_uuid}/actions/disable",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Disabled user: {data['response'].get('username', user_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
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
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/users/{user_uuid}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            logger.info(f"Deleted user: {user_uuid}")
            return True
                
    except Exception as e:
        logger.error(f"Error deleting user {user_uuid}: {e}")
        return False

async def reset_user_traffic(user_uuid: str):
    """Сбросить трафик пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/users/{user_uuid}/actions/reset-traffic",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Reset traffic for user: {data['response'].get('username', user_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
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
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/users/{user_uuid}/actions/revoke",
                headers=headers,
                json={},  # Empty body as per API spec
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Revoked subscription for user: {data['response'].get('username', user_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
                return None
                
    except Exception as e:
        logger.error(f"Error revoking subscription for user {user_uuid}: {e}")
        return None

async def get_users_count():
    """Получить количество пользователей"""
    try:
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            # Получаем только один пользователь для получения общего количества
            response = await client.get(
                f"{API_BASE_URL}/api/users?size=1&start=0",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                return data['response'].get('total', 0)
            else:
                logger.error(f"Unexpected response structure: {data}")
                return 0
                
    except Exception as e:
        logger.error(f"Error getting users count: {e}")
        return 0

async def get_users_stats():
    """Получить статистику пользователей"""
    try:
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/users?size=1000&start=0",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data and 'users' in data['response']:
                total_users = data['response'].get('total', len(data['response']['users']))
                active_users = 0
                
                # Подсчитываем активных пользователей
                for user in data['response']['users']:
                    if user.get('status') == 'ACTIVE':
                        active_users += 1
                
                return {
                    'total': total_users,
                    'active': active_users
                }
            else:
                logger.error(f"Unexpected response structure: {data}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        return None
