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
        sdk = RemnaAPI.get_sdk()
        host: HostResponseDto = await sdk.hosts.create_host(**data)
        logger.info(f"Created host: {host.name}")
        return host
    except Exception as e:
        logger.error(f"Error creating host: {e}")
        return None

async def update_host(host_uuid, data):
    """Обновить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        data["uuid"] = host_uuid
        host: HostResponseDto = await sdk.hosts.update_host(**data)
        logger.info(f"Updated host: {host.name}")
        return host
    except Exception as e:
        logger.error(f"Error updating host {host_uuid}: {e}")
        return None

async def delete_host(host_uuid):
    """Удалить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return False
            
        sdk = RemnaAPI.get_sdk()
        await sdk.hosts.delete_host(uuid=host_uuid)
        logger.info(f"Deleted host: {host_uuid}")
        return True
    except Exception as e:
        logger.error(f"Error deleting host {host_uuid}: {e}")
        return False

async def enable_host(host_uuid):
    """Включить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        host: HostResponseDto = await sdk.hosts.enable_host(uuid=host_uuid)
        logger.info(f"Enabled host: {host.name}")
        return host
    except Exception as e:
        logger.error(f"Error enabling host {host_uuid}: {e}")
        return None

async def disable_host(host_uuid):
    """Отключить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        host: HostResponseDto = await sdk.hosts.disable_host(uuid=host_uuid)
        logger.info(f"Disabled host: {host.name}")
        return host
    except Exception as e:
        logger.error(f"Error disabling host {host_uuid}: {e}")
        return None
    
async def bulk_enable_hosts(uuids):
    """Массово включить хосты по UUID"""
    try:
        if not uuids or not isinstance(uuids, list) or len(uuids) == 0:
            logger.error("Host UUIDs list is empty or invalid")
            return False
            
        sdk = RemnaAPI.get_sdk()
        result = await sdk.hosts.bulk_enable_hosts(uuids=uuids)
        logger.info(f"Bulk enabled {len(uuids)} hosts")
        return result
    except Exception as e:
        logger.error(f"Error bulk enabling hosts: {e}")
        return False

async def bulk_disable_hosts(uuids):
        """Bulk disable hosts by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/disable", data)
    
@staticmethod
async def reorder_hosts(hosts_data):
    """Reorder hosts"""
    return await RemnaAPI.post("hosts/actions/reorder", {"hosts": hosts_data})

@staticmethod
async def bulk_delete_hosts(uuids):
    """Bulk delete hosts by UUIDs"""
    data = {"uuids": uuids}
    return await RemnaAPI.post("hosts/bulk/delete", data)

@staticmethod
async def bulk_set_inbound_to_hosts(uuids, inbound_uuid):
    """Set inbound to hosts by UUIDs"""
    data = {
        "uuids": uuids,
        "inboundUuid": inbound_uuid
    }
    return await RemnaAPI.post("hosts/bulk/set-inbound", data)

@staticmethod
async def bulk_set_port_to_hosts(uuids, port):
    """Set port to hosts by UUIDs"""
    data = {
        "uuids": uuids,
        "port": port
    }
    return await RemnaAPI.post("hosts/bulk/set-port", data)
