import logging
import httpx
from modules.api.client import RemnaAPI
from modules.config import API_BASE_URL, API_TOKEN
from remnawave_api.models import NodeResponseDto, NodeUsageResponseDto

logger = logging.getLogger(__name__)

async def get_all_nodes():
    """Получить все ноды - обходной путь для багованного SDK"""
    try:
        # Используем прямой HTTP запрос вместо SDK
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(headers=headers, verify=False, timeout=30) as client:
            url = f'{API_BASE_URL}/nodes'
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url)
            
            if response.status_code == 200:
                nodes_data = response.json()
                logger.info(f"Retrieved {len(nodes_data)} nodes via direct API")
                return nodes_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting all nodes via direct API: {e}")
        
        # Fallback к SDK если прямой запрос не работает  
        try:
            sdk = RemnaAPI.get_sdk()
            nodes: list[NodeResponseDto] = await sdk.nodes.get_all_nodes()
            logger.info(f"Retrieved {len(nodes)} nodes via SDK fallback")
            return nodes
        except Exception as sdk_error:
            logger.error(f"SDK fallback also failed: {sdk_error}")
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
