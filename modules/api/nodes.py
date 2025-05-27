import logging
from modules.api.client import RemnaAPI
from remnawave_api.models import NodeResponseDto, NodeUsageResponseDto

logger = logging.getLogger(__name__)

async def get_all_nodes():
    """Получить все ноды"""
    try:
        sdk = RemnaAPI.get_sdk()
        # Пробуем разные варианты параметров, чтобы решить проблему с UUID
        try:
            # Вариант 1: Указываем list_type
            nodes: list[NodeResponseDto] = await sdk.nodes.get_all_nodes(list_type="all")
        except Exception as e1:
            logger.warning(f"Failed to get nodes with list_type: {e1}, trying alternative...")
            try:
                # Вариант 2: Без параметров, но с проверкой ответа
                nodes: list[NodeResponseDto] = await sdk.nodes.get_all_nodes()
            except Exception as e2:
                logger.warning(f"Failed to get nodes without params: {e2}, trying with empty uuid...")
                try:
                    # Вариант 3: Передаем пустой UUID, если API его требует
                    nodes: list[NodeResponseDto] = await sdk.nodes.get_all_nodes(uuid="")
                except Exception as e3:
                    logger.error(f"All node retrieval methods failed: {e3}")
                    return []
                
        logger.info(f"Retrieved {len(nodes)} nodes")
        return nodes
    except Exception as e:
        logger.error(f"Error getting all nodes: {e}")
        return []

async def get_node_by_uuid(node_uuid: str):
    """Получить ноду по UUID"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        # Передаем uuid как параметр запроса, а не в URL
        node: NodeResponseDto = await sdk.nodes.get_node_by_uuid(uuid=node_uuid)
        logger.info(f"Retrieved node: {node.name}")
        return node
    except Exception as e:
        logger.error(f"Error getting node {node_uuid}: {e}")
        return None

async def get_node_certificate(node_uuid: str):
    """Получить сертификат ноды"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        # Передаем uuid как именованный параметр
        cert = await sdk.nodes.get_node_certificate(uuid=node_uuid)
        logger.info(f"Retrieved certificate for node: {node_uuid}")
        return cert
    except Exception as e:
        logger.error(f"Error getting certificate for node {node_uuid}: {e}")
        return None

async def get_nodes_usage():
    """Получить использование всех нод"""
    try:
        sdk = RemnaAPI.get_sdk()
        # Добавляем параметры для решения проблемы с UUID
        try:
            # Сначала пробуем без параметров
            usage: list[NodeUsageResponseDto] = await sdk.nodes.get_nodes_usage()
        except Exception as e1:
            logger.warning(f"Failed to get nodes usage: {e1}, trying with additional params...")
            try:
                # Пробуем с пустыми параметрами
                usage: list[NodeUsageResponseDto] = await sdk.nodes.get_nodes_usage(uuid="")
            except Exception as e2:
                logger.error(f"All nodes usage retrieval methods failed: {e2}")
                return []
                
        logger.info(f"Retrieved usage for {len(usage)} nodes")
        return usage
    except Exception as e:
        logger.error(f"Error getting nodes usage: {e}")
        return []

async def enable_node(node_uuid: str):
    """Включить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        node: NodeResponseDto = await sdk.nodes.enable_node(uuid=node_uuid)
        logger.info(f"Enabled node: {node.name}")
        return node
    except Exception as e:
        logger.error(f"Error enabling node {node_uuid}: {e}")
        return None

async def disable_node(node_uuid: str):
    """Отключить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        node: NodeResponseDto = await sdk.nodes.disable_node(uuid=node_uuid)
        logger.info(f"Disabled node: {node.name}")
        return node
    except Exception as e:
        logger.error(f"Error disabling node {node_uuid}: {e}")
        return None
