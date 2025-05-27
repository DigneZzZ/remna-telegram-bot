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

async def get_inbounds():
    """Получить все входящие соединения через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                inbounds_data = response.json()
                logger.info(f"Retrieved {len(inbounds_data)} inbounds")
                return inbounds_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting inbounds: {e}")
        return []

async def get_full_inbounds():
    """Получить входящие соединения с полной информацией"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/full"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                inbounds_data = response.json()
                logger.info(f"Retrieved {len(inbounds_data)} full inbounds")
                return inbounds_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting full inbounds: {e}")
        return []

async def add_inbound_to_users(inbound_uuid):
    """Добавить входящее соединение всем пользователям"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}/add-to-users"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
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
            logger.error("Inbound UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}/remove-from-users"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
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
            logger.error("Inbound UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}/add-to-nodes"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
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
            logger.error("Inbound UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}/remove-from-nodes"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                logger.info(f"Removed inbound {inbound_uuid} from all nodes")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error removing inbound {inbound_uuid} from nodes: {e}")
        return False

async def get_inbound_by_uuid(inbound_uuid):
    """Получить входящее соединение по UUID"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/inbounds/{inbound_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                inbound_data = response.json()
                logger.info(f"Retrieved inbound: {inbound_data.get('name', inbound_uuid)}")
                return inbound_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting inbound {inbound_uuid}: {e}")
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
                if inbound.get('is_active') or inbound.get('status') == 'active':
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
    async def get_full_inbounds():
        return await get_full_inbounds()
    
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
    async def get_inbound_by_uuid(inbound_uuid):
        return await get_inbound_by_uuid(inbound_uuid)
        return await RemnaAPI.post("inbounds/bulk/add-to-nodes", data)
    
    @staticmethod
    async def remove_inbound_from_nodes(inbound_uuid):
        """Remove inbound from all nodes"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/remove-from-nodes", data)
