import logging
import httpx
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

async def get_all_nodes():
    """Получить все ноды через прямой HTTP вызов"""
    try:
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/nodes",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data and isinstance(data['response'], list):
                logger.info(f"Retrieved {len(data['response'])} nodes total")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
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
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/nodes/{node_uuid}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Retrieved node: {data['response'].get('name', node_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting node {node_uuid}: {e}")
        return None

async def enable_node(node_uuid: str):
    """Включить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/nodes/{node_uuid}/actions/enable",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Enabled node: {data['response'].get('name', node_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling node {node_uuid}: {e}")
        return None

async def disable_node(node_uuid: str):
    """Отключить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/nodes/{node_uuid}/actions/disable",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Disabled node: {data['response'].get('name', node_uuid)}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling node {node_uuid}: {e}")
        return None

async def restart_node(node_uuid: str):
    """Перезапустить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return None
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/nodes/{node_uuid}/actions/restart",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data:
                logger.info(f"Restarted node: {node_uuid}")
                return data['response']
            else:
                logger.error(f"Unexpected response structure: {data}")
                return None
                
    except Exception as e:
        logger.error(f"Error restarting node {node_uuid}: {e}")
        return None

async def delete_node(node_uuid: str):
    """Удалить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is empty or None")
            return False
            
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/nodes/{node_uuid}",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            logger.info(f"Deleted node: {node_uuid}")
            return True
                
    except Exception as e:
        logger.error(f"Error deleting node {node_uuid}: {e}")
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
            if node.get('isNodeOnline') or node.get('isConnected'):
                online_nodes += 1
        
        return {
            'total': total_nodes,
            'online': online_nodes
        }
    except Exception as e:
        logger.error(f"Error getting nodes stats: {e}")
        return None
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
