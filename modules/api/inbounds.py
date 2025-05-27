import logging
from modules.api.client import RemnaAPI
from remnawave_api.models import InboundResponseDto

logger = logging.getLogger(__name__)

async def get_inbounds():
    """Получить все входящие соединения"""
    try:
        sdk = RemnaAPI.get_sdk()
        inbounds: list[InboundResponseDto] = await sdk.inbounds.get_all_inbounds()
        logger.info(f"Retrieved {len(inbounds)} inbounds")
        return inbounds
    except Exception as e:
        logger.error(f"Error getting inbounds: {e}")
        return []

async def get_full_inbounds():
    """Получить входящие соединения с полной информацией"""
    try:
        sdk = RemnaAPI.get_sdk()
        inbounds: list[InboundResponseDto] = await sdk.inbounds.get_full_inbounds()
        logger.info(f"Retrieved {len(inbounds)} full inbounds")
        return inbounds
    except Exception as e:
        logger.error(f"Error getting full inbounds: {e}")
        return []

async def add_inbound_to_users(inbound_uuid):
    """Добавить входящее соединение всем пользователям"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return False
            
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.add_inbound_to_users(uuid=inbound_uuid)
        logger.info(f"Added inbound {inbound_uuid} to all users")
        return result
    except Exception as e:
        logger.error(f"Error adding inbound {inbound_uuid} to users: {e}")
        return False
    
async def remove_inbound_from_users(inbound_uuid):
    """Удалить входящее соединение у всех пользователей"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return False
            
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.remove_inbound_from_users(uuid=inbound_uuid)
        logger.info(f"Removed inbound {inbound_uuid} from all users")
        return result
    except Exception as e:
        logger.error(f"Error removing inbound {inbound_uuid} from users: {e}")
        return False

async def add_inbound_to_nodes(inbound_uuid):
    """Добавить входящее соединение всем нодам"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return False
            
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.add_inbound_to_nodes(uuid=inbound_uuid)
        logger.info(f"Added inbound {inbound_uuid} to all nodes")
        return result
    except Exception as e:
        logger.error(f"Error adding inbound {inbound_uuid} to nodes: {e}")
        return False

async def remove_inbound_from_nodes(inbound_uuid):
    """Удалить входящее соединение у всех нод"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return False
            
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.remove_inbound_from_nodes(uuid=inbound_uuid)
        logger.info(f"Removed inbound {inbound_uuid} from all nodes")
        return result
    except Exception as e:
        logger.error(f"Error removing inbound {inbound_uuid} from nodes: {e}")
        return False

async def get_inbound_by_uuid(inbound_uuid):
    """Получить входящее соединение по UUID"""
    try:
        if not inbound_uuid:
            logger.error("Inbound UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        inbound: InboundResponseDto = await sdk.inbounds.get_inbound_by_uuid(uuid=inbound_uuid)
        logger.info(f"Retrieved inbound: {inbound.name}")
        return inbound
    except Exception as e:
        logger.error(f"Error getting inbound {inbound_uuid}: {e}")
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
