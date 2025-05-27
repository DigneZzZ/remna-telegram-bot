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

async def get_all_nodes():
    """Получить все ноды через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f'{API_BASE_URL}/nodes'
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
              if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # Проверяем структуру ответа
                if isinstance(data, dict) and 'nodes' in data:
                    nodes_list = data['nodes']
                elif isinstance(data, list):
                    nodes_list = data
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
                
                logger.info(f"Retrieved {len(nodes_list)} nodes via direct API")
                return nodes_list
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting all nodes: {e}")
        return []

async def get_node_by_uuid(node_uuid: str):
    """Получить ноду по UUID"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                node_data = response.json()
                logger.info(f"Retrieved node: {node_data.get('name', node_uuid)}")
                return node_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting node {node_uuid}: {e}")
        return None

async def get_node_usage(node_uuid: str):
    """Получить статистику использования ноды"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/usage"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                usage_data = response.json()
                logger.info(f"Retrieved usage for node: {node_uuid}")
                return usage_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting node usage {node_uuid}: {e}")
        return None

async def restart_node(node_uuid: str):
    """Перезапустить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/restart"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Restarted node: {node_uuid}")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error restarting node {node_uuid}: {e}")
        return False

async def get_nodes_count():
    """Получить количество нод"""
    try:
        nodes = await get_all_nodes()
        return len(nodes) if nodes else 0
    except Exception as e:
        logger.error(f"Error getting nodes count: {e}")
        return 0

async def get_nodes_stats():
    """Получить статистику нод"""
    try:
        nodes = await get_all_nodes()
        if not nodes:
            return None
            
        total_nodes = len(nodes)
        online_nodes = 0
        
        # Подсчитываем онлайн ноды
        for node in nodes:
            if isinstance(node, dict):
                if node.get('status') == 'online' or node.get('is_online'):
                    online_nodes += 1
        
        return {
            'total': total_nodes,
            'online': online_nodes
        }
    except Exception as e:
        logger.error(f"Error getting nodes stats: {e}")
        return None
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
