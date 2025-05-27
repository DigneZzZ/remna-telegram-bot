import logging
from modules.api.client import RemnaAPI
from remnawave_api.models import HostResponseDto, HostsResponseDto

logger = logging.getLogger(__name__)

async def get_all_hosts(start=None, size=None):
    """Получить все хосты"""
    try:
        sdk = RemnaAPI.get_sdk()
        try:
            # Сначала пробуем без параметров, так как API может не поддерживать их
            response = await sdk.hosts.get_all_hosts()
            logger.info(f"Retrieved hosts successfully")
            return response
        except Exception as e1:
            logger.warning(f"Failed to get hosts without params: {e1}, trying with parameters...")
            try:
                # Если не сработало, пробуем с параметрами
                if start is not None and size is not None:
                    response = await sdk.hosts.get_all_hosts(start=start, size=size)
                else:
                    # В случае если не передали параметры
                    response = await sdk.hosts.get_all_hosts()
                logger.info(f"Retrieved hosts successfully")
                return response
            except Exception as e2:
                logger.error(f"Failed to get hosts with params: {e2}")
                return None
    except Exception as e:
        logger.error(f"Error getting all hosts: {e}")
        return None

async def get_host_by_uuid(host_uuid: str):
    """Получить хост по UUID"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        host: HostResponseDto = await sdk.hosts.get_host_by_uuid(uuid=host_uuid)
        logger.info(f"Retrieved host: {host.name}")
        return host
    except Exception as e:
        logger.error(f"Error getting host {host_uuid}: {e}")
        return None
    
async def create_host(data):
    """Создать новый хост"""
    try:
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
