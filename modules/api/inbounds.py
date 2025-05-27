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

async def get_inbounds():
    """Получить все входящие соединения через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # API может возвращать данные в формате {'response': [...]}
                if isinstance(data, dict) and 'response' in data:
                    inbounds_list = data['response']
                    logger.info(f"Retrieved {len(inbounds_list)} inbounds from response")
                    return inbounds_list
                elif isinstance(data, list):
                    logger.info(f"Retrieved {len(data)} inbounds from direct list")
                    return data
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting inbounds: {e}")
        return []

# Alias для совместимости с handlers
async def get_all_inbounds():
    """Alias для get_inbounds() для совместимости с handlers"""
    return await get_inbounds()

async def get_full_inbounds():
    """Получить входящие соединения с полной информацией"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/full"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # API может возвращать данные в формате {'response': [...]}
                if isinstance(data, dict) and 'response' in data:
                    inbounds_list = data['response']
                    logger.info(f"Retrieved {len(inbounds_list)} full inbounds from response")
                    return inbounds_list
                elif isinstance(data, list):
                    logger.info(f"Retrieved {len(data)} full inbounds from direct list")
                    return data
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting full inbounds: {e}")
        return []

async def get_inbound_by_uuid(inbound_uuid):
    """Получить входящее соединение по UUID"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved inbound {inbound_uuid} successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting inbound {inbound_uuid}: {e}")
        return None

async def create_inbound(inbound_data):
    """Создать новое входящее соединение"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds"
            logger.info(f"Making direct API call to create inbound: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=inbound_data)
            
            if response.status_code in [200, 201]:
                new_inbound = response.json()
                logger.info(f"Inbound created successfully with UUID: {new_inbound.get('uuid', 'unknown')}")
                return new_inbound
            else:
                logger.error(f"Failed to create inbound. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating inbound: {e}")
        return None

async def update_inbound(inbound_uuid, inbound_data):
    """Обновить входящее соединение"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}"
            logger.info(f"Making direct API call to update inbound: {url}")
            
            response = await client.put(url, headers=_get_headers(), json=inbound_data)
            
            if response.status_code == 200:
                updated_inbound = response.json()
                logger.info(f"Inbound {inbound_uuid} updated successfully")
                return updated_inbound
            else:
                logger.error(f"Failed to update inbound {inbound_uuid}. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error updating inbound {inbound_uuid}: {e}")
        return None

async def delete_inbound(inbound_uuid):
    """Удалить входящее соединение"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}"
            logger.info(f"Making direct API call to delete inbound: {url}")
            
            response = await client.delete(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"Inbound {inbound_uuid} deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete inbound {inbound_uuid}. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting inbound {inbound_uuid}: {e}")
        return False

async def add_inbound_to_users(inbound_uuid):
    """Добавить входящее соединение всем пользователям"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/bulk/add-to-users"
            data = {"inboundUuid": inbound_uuid}
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Added inbound {inbound_uuid} to all users")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error adding inbound {inbound_uuid} to users: {e}")
        return False

async def remove_inbound_from_users(inbound_uuid):
    """Удалить входящее соединение у всех пользователей"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/bulk/remove-from-users"
            data = {"inboundUuid": inbound_uuid}
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Removed inbound {inbound_uuid} from all users")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error removing inbound {inbound_uuid} from users: {e}")
        return False

async def add_inbound_to_nodes(inbound_uuid):
    """Добавить входящее соединение всем нодам"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/bulk/add-to-nodes"
            data = {"inboundUuid": inbound_uuid}
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Added inbound {inbound_uuid} to all nodes")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error adding inbound {inbound_uuid} to nodes: {e}")
        return False

async def remove_inbound_from_nodes(inbound_uuid):
    """Удалить входящее соединение у всех нод"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/bulk/remove-from-nodes"
            data = {"inboundUuid": inbound_uuid}
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Removed inbound {inbound_uuid} from all nodes")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error removing inbound {inbound_uuid} from nodes: {e}")
        return False

async def enable_inbound(inbound_uuid):
    """Включить входящее соединение"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}/enable"
            logger.info(f"Making direct API call to enable inbound: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                inbound_data = response.json()
                logger.info(f"Inbound {inbound_uuid} enabled successfully")
                return inbound_data
            else:
                logger.error(f"Failed to enable inbound {inbound_uuid}. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling inbound {inbound_uuid}: {e}")
        return None

async def disable_inbound(inbound_uuid):
    """Отключить входящее соединение"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}/disable"
            logger.info(f"Making direct API call to disable inbound: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                inbound_data = response.json()
                logger.info(f"Inbound {inbound_uuid} disabled successfully")
                return inbound_data
            else:
                logger.error(f"Failed to disable inbound {inbound_uuid}. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling inbound {inbound_uuid}: {e}")
        return None

async def get_inbounds_count():
    """Получить количество входящих соединений"""
    try:
        inbounds = await get_inbounds()
        return len(inbounds) if inbounds else 0
    except Exception as e:
        logger.error(f"Error getting inbounds count: {e}")
        return 0

async def get_inbounds_stats():
    """Получить статистику входящих соединений"""
    try:
        inbounds = await get_inbounds()
        if not inbounds:
            return None
            
        total_inbounds = len(inbounds)
        active_inbounds = 0
        
        # Подсчитываем активные входящие соединения
        for inbound in inbounds:
            if isinstance(inbound, dict):
                # Проверяем различные поля для определения активности
                if (inbound.get('isEnabled') or 
                    inbound.get('is_enabled') or 
                    inbound.get('status') == 'active' or
                    inbound.get('enabled')):
                    active_inbounds += 1
        
        return {
            'total': total_inbounds,
            'active': active_inbounds
        }
    except Exception as e:
        logger.error(f"Error getting inbounds stats: {e}")
        return None

# Для обратной совместимости
class InboundAPI:
    """API methods for inbound management - Legacy compatibility class"""
    
    @staticmethod
    async def get_inbounds():
        return await get_inbounds()
    
    @staticmethod
    async def get_all_inbounds():
        return await get_all_inbounds()
    
    @staticmethod
    async def get_full_inbounds():
        return await get_full_inbounds()
    
    @staticmethod
    async def create_inbound(inbound_data):
        return await create_inbound(inbound_data)
    
    @staticmethod
    async def update_inbound(inbound_uuid, inbound_data):
        return await update_inbound(inbound_uuid, inbound_data)
    
    @staticmethod
    async def delete_inbound(inbound_uuid):
        return await delete_inbound(inbound_uuid)
    
    @staticmethod
    async def get_inbound_by_uuid(inbound_uuid):
        return await get_inbound_by_uuid(inbound_uuid)
    
    @staticmethod
    async def add_inbound_to_users(inbound_uuid):
        return await add_inbound_to_users(inbound_uuid)
    
    @staticmethod
    async def remove_inbound_from_users(inbound_uuid):
        return await remove_inbound_from_users(inbound_uuid)
    
    @staticmethod
    async def add_inbound_to_nodes(inbound_uuid):
        return await add_inbound_to_nodes(inbound_uuid)
    
    @staticmethod
    async def remove_inbound_from_nodes(inbound_uuid):
        return await remove_inbound_from_nodes(inbound_uuid)
    
    @staticmethod
    async def enable_inbound(inbound_uuid):
        return await enable_inbound(inbound_uuid)
    
    @staticmethod
    async def disable_inbound(inbound_uuid):
        return await disable_inbound(inbound_uuid)
    
    @staticmethod
    async def get_inbounds_count():
        return await get_inbounds_count()
    
    @staticmethod
    async def get_inbounds_stats():
        return await get_inbounds_stats()

logger.info("Inbounds API module loaded successfully")