import logging
from modules.api.client import RemnaAPI
from remnawave_api.models import NodeResponseDto, NodeUsageResponseDto

logger = logging.getLogger(__name__)

async def get_all_nodes():
    """Получить все ноды"""
    try:
        sdk = get_remnawave_sdk()
        nodes: list[NodeResponseDto] = await sdk.nodes.get_all_nodes()
        logger.info(f"Retrieved {len(nodes)} nodes")
        return nodes
    except Exception as e:
        logger.error(f"Error getting all nodes: {e}")
        return []

async def get_node_by_uuid(node_uuid: str):
    """Получить ноду по UUID"""
    try:
        sdk = get_remnawave_sdk()
        node: NodeResponseDto = await sdk.nodes.get_node_by_uuid(node_uuid)
        logger.info(f"Retrieved node: {node.name}")
        return node
    except Exception as e:
        logger.error(f"Error getting node {node_uuid}: {e}")
        return None

async def get_node_certificate(node_uuid: str):
    """Получить сертификат ноды"""
    try:
        sdk = get_remnawave_sdk()
        cert = await sdk.nodes.get_node_certificate(node_uuid)
        logger.info(f"Retrieved certificate for node: {node_uuid}")
        return cert
    except Exception as e:
        logger.error(f"Error getting certificate for node {node_uuid}: {e}")
        return None

async def get_nodes_usage():
    """Получить использование всех нод"""
    try:
        sdk = get_remnawave_sdk()
        usage: list[NodeUsageResponseDto] = await sdk.nodes.get_nodes_usage()
        logger.info(f"Retrieved usage for {len(usage)} nodes")
        return usage
    except Exception as e:
        logger.error(f"Error getting nodes usage: {e}")
        return []

async def enable_node(node_uuid: str):
    """Включить ноду"""
    try:
        sdk = get_remnawave_sdk()
        node: NodeResponseDto = await sdk.nodes.enable_node(node_uuid)
        logger.info(f"Enabled node: {node.name}")
        return node
    except Exception as e:
        logger.error(f"Error enabling node {node_uuid}: {e}")
        return None

async def disable_node(node_uuid: str):
    """Отключить ноду"""
    try:
        sdk = get_remnawave_sdk()
        node: NodeResponseDto = await sdk.nodes.disable_node(node_uuid)
        logger.info(f"Disabled node: {node.name}")
        return node
    except Exception as e:
        logger.error(f"Error disabling node {node_uuid}: {e}")
        return None