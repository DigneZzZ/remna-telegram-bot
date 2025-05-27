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
    """Получить всех пользователей через прямой HTTP вызов без ограничений"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # Запросим большое количество пользователей или используем параметры для получения всех
            # Попробуем разные варианты параметров для получения всех пользователей
            all_users = []
            page = 0
            page_size = 1000  # Большой размер страницы
            
            while True:
                # Попробуем разные варианты параметров пагинации
                params = {
                    'page': page,
                    'size': page_size,
                    'limit': page_size,
                    'offset': page * page_size
                }
                
                url = f"{API_BASE_URL}/users"
                logger.info(f"Making direct API call to: {url} with params: {params}")
                
                response = await client.get(url, headers=_get_headers(), params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                    
                    current_users = []
                    total_count = None
                    
                    # API возвращает данные в формате {'response': {'total': X, 'users': [...]}}
                    if isinstance(data, dict) and 'response' in data:
                        response_data = data['response']
                        if isinstance(response_data, dict):
                            if 'users' in response_data:
                                current_users = response_data['users']
                                total_count = response_data.get('total')
                            elif 'data' in response_data:
                                current_users = response_data['data']
                                total_count = response_data.get('total')
                        elif isinstance(response_data, list):
                            current_users = response_data
                    elif isinstance(data, dict) and 'users' in data:
                        current_users = data['users']
                        total_count = data.get('total')
                    elif isinstance(data, list):
                        current_users = data
                    else:
                        logger.error(f"Unexpected API response structure: {type(data)}")
                        break
                    
                    if not current_users:
                        logger.info("No more users found, breaking pagination loop")
                        break
                    
                    all_users.extend(current_users)
                    logger.info(f"Retrieved {len(current_users)} users on page {page}, total so far: {len(all_users)}")
                    
                    # Если получили меньше пользователей чем запрашивали, значит это последняя страница
                    if len(current_users) < page_size:
                        logger.info("Received fewer users than page size, assuming last page")
                        break
                    
                    # Если знаем общее количество и уже получили всех
                    if total_count and len(all_users) >= total_count:
                        logger.info(f"Retrieved all {total_count} users")
                        break
                    
                    page += 1
                    
                    # Защита от бесконечного цикла
                    if page > 100:
                        logger.warning("Reached maximum page limit (100), breaking loop")
                        break
                        
                else:
                    logger.error(f"API call failed with status {response.status_code}: {response.text}")
                    # Если первый запрос с параметрами не удался, попробуем без параметров
                    if page == 0:
                        logger.info("Trying request without pagination parameters")
                        response = await client.get(f"{API_BASE_URL}/users", headers=_get_headers())
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, dict) and 'response' in data:
                                response_data = data['response']
                                if isinstance(response_data, dict) and 'users' in response_data:
                                    all_users = response_data['users']
                                elif isinstance(response_data, list):
                                    all_users = response_data
                            elif isinstance(data, list):
                                all_users = data
                            logger.info(f"Retrieved {len(all_users)} users without pagination")
                        else:
                            logger.error(f"Fallback request also failed: {response.status_code}")
                    break
            
            logger.info(f"Total users retrieved: {len(all_users)}")
            return all_users
                
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

async def get_users_with_large_limit():
    """Альтернативный метод получения пользователей с большим лимитом"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # Попробуем разные параметры для получения большого количества пользователей
            params_variants = [
                {'size': 10000},  # Большой size
                {'limit': 10000}, # Большой limit
                {'per_page': 10000}, # per_page
                {'count': 10000}, # count
                {'size': 10000, 'page': 0},
                {'limit': 10000, 'offset': 0},
                {}  # Без параметров
            ]
            
            for params in params_variants:
                url = f"{API_BASE_URL}/users"
                logger.info(f"Trying API call with params: {params}")
                
                response = await client.get(url, headers=_get_headers(), params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    users_list = []
                    # Парсим ответ
                    if isinstance(data, dict) and 'response' in data:
                        response_data = data['response']
                        if isinstance(response_data, dict) and 'users' in response_data:
                            users_list = response_data['users']
                        elif isinstance(response_data, list):
                            users_list = response_data
                    elif isinstance(data, dict) and 'users' in data:
                        users_list = data['users']
                    elif isinstance(data, list):
                        users_list = data
                    
                    if users_list:
                        logger.info(f"Successfully retrieved {len(users_list)} users with params: {params}")
                        return users_list
                else:
                    logger.debug(f"Request with params {params} failed: {response.status_code}")
            
            logger.warning("All parameter variants failed")
            return []
                
    except Exception as e:
        logger.error(f"Error getting users with large limit: {e}")
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
                
                # Парсим ответ API
                if isinstance(new_user, dict) and 'response' in new_user:
                    return new_user['response']
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
                
                # Парсим ответ API
                if isinstance(updated_user, dict) and 'response' in updated_user:
                    return updated_user['response']
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
                
                # Парсим ответ API
                if isinstance(user_data, dict) and 'response' in user_data:
                    return user_data['response']
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
                
                # Парсим ответ API
                if isinstance(user_data, dict) and 'response' in user_data:
                    return user_data['response']
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
        # Попробуем сначала более эффективный способ получения только счетчика
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # Пробуем endpoints которые могут вернуть только статистику
            stats_endpoints = [
                f"{API_BASE_URL}/users/count",
                f"{API_BASE_URL}/users/stats", 
                f"{API_BASE_URL}/stats/users"
            ]
            
            for endpoint in stats_endpoints:
                try:
                    response = await client.get(endpoint, headers=_get_headers())
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Ищем счетчик в различных форматах ответа
                        count_value = None
                        if isinstance(data, dict):
                            if 'response' in data:
                                response_data = data['response']
                                count_value = (response_data.get('count') or 
                                             response_data.get('total') or 
                                             response_data.get('totalUsers'))
                            else:
                                count_value = (data.get('count') or 
                                             data.get('total') or 
                                             data.get('totalUsers'))
                        elif isinstance(data, (int, float)):
                            count_value = int(data)
                        
                        if count_value is not None:
                            logger.info(f"Got users count from {endpoint}: {count_value}")
                            return int(count_value)
                except Exception as e:
                    logger.debug(f"Stats endpoint {endpoint} failed: {e}")
            
            # Если статистические endpoints не работают, получаем всех пользователей
            users = await get_all_users()
            count = len(users) if users else 0
            logger.info(f"Got users count by fetching all users: {count}")
            return count
            
    except Exception as e:
        logger.error(f"Error getting users count: {e}")
        return 0

async def get_users_stats():
    """Получить статистику пользователей"""
    try:
        # Попробуем получить статистику напрямую
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            stats_endpoints = [
                f"{API_BASE_URL}/users/stats",
                f"{API_BASE_URL}/stats/users",
                f"{API_BASE_URL}/dashboard/stats"
            ]
            
            for endpoint in stats_endpoints:
                try:
                    response = await client.get(endpoint, headers=_get_headers())
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Парсим статистику из ответа
                        if isinstance(data, dict):
                            stats_data = data.get('response', data)
                            if all(key in stats_data for key in ['total', 'active']):
                                logger.info(f"Got users stats from {endpoint}")
                                return stats_data
                except Exception as e:
                    logger.debug(f"Stats endpoint {endpoint} failed: {e}")
        
        # Если прямые endpoints не работают, вычисляем статистику из всех пользователей
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
        
        stats = {
            'total': total_users,
            'active': active_users,
            'expired': expired_users,
            'total_traffic': total_traffic
        }
        
        logger.info(f"Calculated users stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        return None