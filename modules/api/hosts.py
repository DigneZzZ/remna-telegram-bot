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

async def get_all_hosts(start=None, size=None):
    """Получить все хосты через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                hosts_data = response.json()
                logger.info(f"Retrieved hosts successfully: {len(hosts_data) if isinstance(hosts_data, list) else 'Unknown count'}")
                return hosts_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting all hosts: {e}")
        return []

async def get_host_by_uuid(host_uuid: str):
    """Получить хост по UUID"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                host_data = response.json()
                logger.info(f"Retrieved host: {host_data.get('name', host_uuid)}")
                return host_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting host {host_uuid}: {e}")
        return None
    
async def create_host(data):
    """Создать новый хост"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                host_data = response.json()
                logger.info(f"Created host: {host_data.get('name', 'Unknown')}")
                return host_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating host: {e}")
        return None

async def update_host(host_uuid, data):
    """Обновить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.put(url, headers=_get_headers(), json=data)
            
            if response.status_code == 200:
                host_data = response.json()
                logger.info(f"Updated host: {host_data.get('name', host_uuid)}")
                return host_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error updating host {host_uuid}: {e}")
        return None

async def delete_host(host_uuid):
    """Удалить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.delete(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"Deleted host: {host_uuid}")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting host {host_uuid}: {e}")
        return False

async def enable_host(host_uuid):
    """Включить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/enable"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code == 200:
                host_data = response.json()
                logger.info(f"Enabled host: {host_data.get('name', host_uuid)}")
                return host_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling host {host_uuid}: {e}")
        return None

async def disable_host(host_uuid):
    """Отключить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/disable"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code == 200:
                host_data = response.json()
                logger.info(f"Disabled host: {host_data.get('name', host_uuid)}")
                return host_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling host {host_uuid}: {e}")
        return None
    
async def bulk_enable_hosts(uuids):
    """Массово включить хосты по UUID"""
    try:
        if not uuids or not isinstance(uuids, list) or len(uuids) == 0:
            logger.error("Host UUIDs list is empty or invalid")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/bulk/enable"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json={"uuids": uuids})
            
            if response.status_code in [200, 201]:
                logger.info(f"Bulk enabled {len(uuids)} hosts")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error bulk enabling hosts: {e}")
        return False

async def bulk_disable_hosts(uuids):
    """Массово отключить хосты по UUID"""
    try:
        if not uuids or not isinstance(uuids, list) or len(uuids) == 0:
            logger.error("Host UUIDs list is empty or invalid")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/bulk/disable"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers(), json={"uuids": uuids})
            
            if response.status_code in [200, 201]:
                logger.info(f"Bulk disabled {len(uuids)} hosts")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error bulk disabling hosts: {e}")
        return False

async def get_hosts_count():
    """Получить количество хостов"""
    try:
        hosts = await get_all_hosts()
        return len(hosts) if hosts else 0
    except Exception as e:
        logger.error(f"Error getting hosts count: {e}")
        return 0

async def get_hosts_stats():
    """Получить статистику хостов"""
    try:
        hosts = await get_all_hosts()
        if not hosts:
            return None
            
        total_hosts = len(hosts)
        active_hosts = 0
        
        # Подсчитываем активные хосты
        for host in hosts:
            if isinstance(host, dict):
                if host.get('is_active') or host.get('status') == 'active':
                    active_hosts += 1
        
        return {
            'total': total_hosts,
            'active': active_hosts
        }
    except Exception as e:
        logger.error(f"Error getting hosts stats: {e}")
        return None
