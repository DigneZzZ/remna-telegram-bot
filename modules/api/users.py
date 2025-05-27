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
            logger.error("User UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/users/{user_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Retrieved user {user_uuid} successfully")
                return user_data
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
