import logging
import httpx
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
            url = f"{API_BASE_URL}/users"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # API возвращает данные в формате {'response': {'total': X, 'users': [...]}}
                if isinstance(data, dict) and 'response' in data:
                    response_data = data['response']
                    if isinstance(response_data, dict) and 'users' in response_data:
                        users_list = response_data['users']
                        logger.info(f"Retrieved {len(users_list)} users from response.users")
                        return users_list
                    elif isinstance(response_data, list):
                        users_list = response_data
                        logger.info(f"Retrieved {len(users_list)} users from response list")
                        return users_list
                    else:
                        logger.error(f"Unexpected response structure in 'response' field: {type(response_data)}")
                        return []
                elif isinstance(data, dict) and 'users' in data:
                    users_list = data['users']
                    logger.info(f"Retrieved {len(users_list)} users from data.users")
                    return users_list
                elif isinstance(data, list):
                    users_list = data
                    logger.info(f"Retrieved {len(users_list)} users from data list")
                    return users_list
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
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
            logger.error("User UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved user {user_uuid} successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting user by UUID {user_uuid}: {e}")
        return None

async def create_user(user_data: dict):
    """Создать нового пользователя"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users"
            logger.info(f"Making direct API call to create user: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=user_data)
            
            if response.status_code in [200, 201]:
                new_user = response.json()
                logger.info(f"User created successfully with UUID: {new_user.get('uuid', 'unknown')}")
                return new_user
            else:
                logger.error(f"Failed to create user. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

async def update_user(user_uuid: str, user_data: dict):
    """Обновить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}"
            logger.info(f"Making direct API call to update user: {url}")
            
            response = await client.put(url, headers=_get_headers(), json=user_data)
            
            if response.status_code == 200:
                updated_user = response.json()
                logger.info(f"User {user_uuid} updated successfully")
                return updated_user
            else:
                logger.error(f"Failed to update user {user_uuid}. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error updating user {user_uuid}: {e}")
        return None

async def delete_user(user_uuid: str):
    """Удалить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}"
            logger.info(f"Making direct API call to delete user: {url}")
            
            response = await client.delete(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"User {user_uuid} deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete user {user_uuid}. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting user {user_uuid}: {e}")
        return False

async def enable_user(user_uuid: str):
    """Включить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}/enable"
            logger.info(f"Making direct API call to enable user: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                user_data = response.json()
                logger.info(f"User {user_uuid} enabled successfully")
                return user_data
            else:
                logger.error(f"Failed to enable user {user_uuid}. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling user {user_uuid}: {e}")
        return None

async def disable_user(user_uuid: str):
    """Отключить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}/disable"
            logger.info(f"Making direct API call to disable user: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                user_data = response.json()
                logger.info(f"User {user_uuid} disabled successfully")
                return user_data
            else:
                logger.error(f"Failed to disable user {user_uuid}. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling user {user_uuid}: {e}")
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
        expired_users = 0
        total_traffic = 0
        
        from datetime import datetime
        now = datetime.now()
        
        for user in users:
            if isinstance(user, dict):
                # Проверяем активность по статусу
                status = user.get('status', '').upper()
                if status == 'ACTIVE':
                    active_users += 1
                
                # Проверяем истекшие по expireAt
                expire_at = user.get('expireAt') or user.get('expire_at')
                if expire_at:
                    try:
                        # Удаляем Z и миллисекунды если есть
                        expire_str = expire_at.replace('Z', '').split('.')[0]
                        expire_date = datetime.fromisoformat(expire_str)
                        if expire_date < now:
                            expired_users += 1
                    except Exception as date_error:
                        logger.debug(f"Error parsing date {expire_at}: {date_error}")
                
                # Суммируем трафик
                used_traffic = user.get('usedTraffic') or user.get('used_traffic', 0)
                if used_traffic:
                    total_traffic += used_traffic
        
        return {
            'total': total_users,
            'active': active_users,
            'expired': expired_users,
            'total_traffic': total_traffic
        }
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        return None